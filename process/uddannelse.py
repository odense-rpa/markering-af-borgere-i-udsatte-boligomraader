def tilføj_uddannelsesmarkering(markering: str, borgers_uddannelsesniveau: list) -> str:
    """
    Tilføj uddannelses markering til markerings strengen.
    
    Tilføjer numeriske markeringer baseret på borgerens uddannelsesniveau:
    - " 1" for videregående uddannelse (bachelor, master, PhD)
    - " 2" for erhvervsuddannelse
    - " 3" ellers
    """
    VIDEREGAAENDE = {
        'Kort videregående uddannelse',
        'Mellemlang videregående uddannelse',
        'Lang videregående uddannelse',
        'Ph.d.',
    }

    ERHVERV = {
        'faglært',
        'Erhvervsuddannelse',
        'Erhvervsuddannelser',
    }

    niveauer = {udd["levelName"] for udd in borgers_uddannelsesniveau}

    if niveauer & VIDEREGAAENDE:
        markering += " 1"

    if niveauer & ERHVERV:
        markering += " 2"
    else:
        markering += " 3"

    return markering
