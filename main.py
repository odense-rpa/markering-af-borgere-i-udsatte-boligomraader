import argparse
import os
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone, date

from odk_tools.tracking import Tracker
from momentum_client.manager import MomentumClientManager
from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential, WorkItemStatus
from process.config import load_excel_sheet
from process.uddannelse import tilføj_uddannelsesmarkering
from process.sagsbehandler import tildel_sagsbehandler_og_opret_opgave

tracker: Tracker
momentum: MomentumClientManager
proces_navn = "Markering af borgere i udsatte boligområder"

adresser: list[str] 

async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")

    # sætter filtre op til at finde 6.1 & 6.2 borgere, der har startet målgruppen indenfor 15 dage
    filters = [
        {
            "customFilter": "",
            "fieldName": "targetGroupCode",
            "values": [
                "6.1",
                "6.2",
            ]
        },
        {
            "fieldName" : "targetGroupStartDate",
            "values" : [
                (datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%SZ"),
                (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%SZ"),
                "false"
            ]
        }
    ]   
    borgere = momentum.borgere.hent_borgere(filters=filters)

    for borger in borgere["data"]:
        borger_info = momentum.borgere.hent_borger(borger["cpr"])
        borger_adresse = (
            borger_info.get("contactInformation", {}).get("primaryAddress", {}).get("street", "") +
            " " +
            borger_info.get("contactInformation", {}).get("primaryAddress", {}).get("building", "")
        )

        # check om borgerens adresse er i excel listen - ellers skip borger
        if not borger_adresse.strip() in [b.adresse for b in adresser]:
            continue

        # finder den markeringsgruppe, der passer til borgerens adresse
        passende_markering = [b.markering for b in adresser if b.adresse == borger_adresse.strip()]
        if not passende_markering:
            ValueError(f"Kunne ikke finde passende markering for borger med adresse {borger_adresse}")

        # hvis borgere har opgaven og fået den inden for 30 dage, så skip borger
        borgers_opgaver = momentum.opgaver.hent_opgaver(borger_info)
        if any(opgave for opgave in borgers_opgaver if opgave["title"] in ["Nye borgere", "Nye borgere - ingen uddannelse"] and datetime.fromisoformat(opgave["deadline"]) >= (datetime.now(timezone.utc) - timedelta(days=30))):
            logger.info(f"Borger {borger['cpr']} har allerede en aktiv opgave - springer over")
            continue

        data = {
            "cpr": borger["cpr"],
            "målgruppe": borger.get("targetGroupCode", ""),
            "markering": passende_markering[0],
        }
        
        workqueue.add_item(
            data=data,
            reference=data["cpr"],
        )
        
        print("stop2")

    print("stop")   


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    sagsbehandlere = [
         {"Initialer": "rmp", "Navn": "Rikke Mahler Pedersen", "Målgruppe": "6.1"},
         {"Initialer": "amich", "Navn": "Ania Minna Smücher Christiansen", "Målgruppe": "6.2"}
     ]


    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
            ingen_uddannelse = False
            markering = data["markering"]
            try:
                borger = momentum.borgere.hent_borger(data["cpr"])
                # TESTBORGER
                # borger = momentum.borgere.hent_borger("0706919079") # falsk cpr

                borgers_uddannelsesniveau = momentum.borgere.hent_uddannelser(borger)
                # Hvis borger ikke har nogen uddannelse, så skal vi oprette speciel opgave
                if not borgers_uddannelsesniveau: 
                    ingen_uddannelse = True
                
                # Tilføjer korrekt sagsbehandler og opretter opgave til denne
                tildel_sagsbehandler_og_opret_opgave(
                    momentum, borger, data, sagsbehandlere, ingen_uddannelse
                )
                # Finder den korrekte markering baseret på borgers uddannelsesniveau
                markering = tilføj_uddannelsesmarkering(markering, borgers_uddannelsesniveau)

                # Henter borgers markeringer
                borgers_markeringer = momentum.borgere.hent_markeringer(borger)

                # Se om markeringen allerede findes
                if not any(m for m in borgers_markeringer if m["tag"]["end"] == None and m["tag"]["title"] == markering):
                    # Tilføj markering til borger
                    momentum.borgere.opret_markering(
                        borger=borger,
                        markeringsnavn=markering,
                        start_dato=date.today()
                    )
                    tracker.track_task(process_name=proces_navn)

            except WorkItemError as e:
                # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                logger.error(f"Error processing item: {data}. Error: {e}")
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    parser = argparse.ArgumentParser(description=proces_navn)
    parser.add_argument(
        "--excel-file", 
        default="./Boligadresser.xlsx", 
        help="Populate the workqueue instead of processing it"
        )
    
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Populate the queue with test data and exit",
    )
    args = parser.parse_args()

    adresser = load_excel_sheet(args.excel_file)

    # Validate Excel file exists
    if not os.path.isfile(args.excel_file):
        raise FileNotFoundError(f"Excel file not found: {args.excel_file}")

    # Initialize external systems for automation here..
    tracking_credential = Credential.get_credential("Odense SQL Server")
    momentum_credential = Credential.get_credential("Momentum - produktion")
    # momentum_credential = Credential.get_credential("Momentum - edu")

    tracker = Tracker(
        username=tracking_credential.username,
        password=tracking_credential.password
    )

    momentum = MomentumClientManager(
        base_url=momentum_credential.data["base_url"],
        client_id=momentum_credential.username,
        client_secret=momentum_credential.password,
        api_key=momentum_credential.data["api_key"],
        resource=momentum_credential.data["resource"],
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
