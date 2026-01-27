def tildel_sagsbehandler_og_opret_opgave(momentum, borger, data, sagsbehandlere, ingen_uddannelse):
    """
    Assign case handler to citizen and create follow-up task.
    
    Finds the appropriate case handler based on target group, updates the citizen's 
    responsible person, and creates a task with conditional description based on 
    whether education information was found.
    """
    # Find sagsbehandler ud fra målgruppe
    sagsbehandler = next((s for s in sagsbehandlere if s["Målgruppe"] == data["målgruppe"]), None)
    if not sagsbehandler:
        raise ValueError(f"Kunne ikke finde sagsbehandler for målgruppe {data['målgruppe']}")
    
    # Hent sagsbehandler
    sagsbehandler = momentum.borgere.hent_sagsbehandler(sagsbehandler["Initialer"])
    momentum.borgere.opdater_borgers_ansvarlige_og_kontaktpersoner(
        borger,
        medarbejderid=sagsbehandler["id"],
    )
    
    if ingen_uddannelse:
        opgave_titel = "Nye borgere - ingen uddannelse"
        opgave_beskrivelse = "Vi fandt ingen uddannelse på denne borger"
    
    opgave = momentum.opgaver.opret_opgave(
        borger,
        medarbejdere=sagsbehandler,
        title=opgave_titel if ingen_uddannelse else "Nye borgere",
        beskrivelse=opgave_beskrivelse if ingen_uddannelse else "RPA har fundet ny borger til dig :-)",
    )
    
    return opgave
