def tilføj_uddannelsesmarkering(markering: str, borgers_uddannelsesniveau: list) -> str:
    """
    Tilføj uddannelses markering til markerings strengen.
    
    Tilføjer numeriske markeringer baseret på borgerens uddannelsesniveau:
    - " 1" for videregående uddannelse (bachelor, master, PhD)
    - " 2" for erhvervsuddannelse
    - " 3" ellers
    """
    if not borgers_uddannelsesniveau:
        return markering + " 3"
    
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
        return markering + " 1"

    if niveauer & ERHVERV:
        return markering + " 2"
    
    return markering + " 3"
