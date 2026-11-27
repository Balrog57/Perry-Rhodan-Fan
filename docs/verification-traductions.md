# Vérification des traductions — suivi de la phase 1

Objectif : texte complet, français lisible, absence de passages non traduits et de résidus techniques. La vérification approfondie de la fidélité viendra ensuite. Un contrôle automatique ou une correction ponctuelle ne vaut pas validation complète d’un numéro.

## Périmètre et sources

- 1 950 fichiers : numéros 0600–0649 et 1200–3099, dans `src/content/chapitres`.
- Originaux : `\\192.168.1.150\Media\Livres\EBOOK\Perry Rhodan Sammelband` ; accès confirmé le 27 novembre 2026.
- Les EPUB individuels 3055 et 3077 ne figurent pas dans l’inventaire initial de ce dossier ; rechercher d’autres exemplaires avant de conclure à une source absente.
- Attention : dans le recueil 2600–2699, le fichier interne `Band2269.html` correspond au roman 2669. Ne pas déduire les correspondances uniquement des noms internes.

## Corrections ciblées vérifiées sur l’original

Les passages corrigés seulement, pas les numéros entiers : 2547, 2586, 2599, 2668, 2669, 2701, 2737, 2759, 2848, 2871, 2874, 2887, 2908, 2909, 2936, 2962, 2983, 3008. Dans les numéros 2737 et 2871, des phrases supplémentaires absentes ont été rétablies après examen du contexte source.

Les résidus allemands courts suivants ont été corrigés par lecture du contexte français : 1401, 1608, 1710, 1738, 1789, 1801, 1813, 1831, 1842, 1932, 1933. Ils ne constituent pas une validation des romans.

## Deuxième lot — consignes insérées dans les textes

Passages contrôlés et corrigés à partir des originaux dans les numéros 1888, 1986, 2028, 2031, 2045, 2082, 2120, 2124, 2134, 2139, 2150, 2162, 2212, 2224, 2225, 2232, 2233, 2248, 2259, 2261, 2262, 2264, 2265, 2280, 2292, 2308, 2309, 2314, 2328, 2329, 2333, 2336, 2343, 2346, 2348, 2370, 2536, 2938, 2942, 2987 et 2991. La recherche ciblée des formulations « réponse précédente était encore en allemand », « segments encore invalides » et « les marqueurs manquent ou le compte est faux » ne trouve plus d’occurrence dans les fichiers locaux après ces corrections. Elle ne détecte pas nécessairement d’autres formulations.

Ces corrections concernent seulement les passages signalés et leur contexte immédiat. Par exemple, la précision sur l’attaque du 2162 et le mécanisme évoqué dans le 2536 ont été rétablis. Aucun de ces numéros n’est pour autant considéré entièrement vérifié.

## Lot 600–604 : alignement pilote

Chaque numéro a été relié à son texte dans le recueil allemand par l’ordre de lecture de l’EPUB. Les paragraphes et blocs français ont été comparés par similarité multilingue LaBSE puis alignés dans l’ordre. Les éléments allemands non appariés étaient exclusivement des séparateurs de scène (`*`) ; leurs voisins ont été contrôlés et les séparateurs replacés dans les fichiers français.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis | Autre bloc FR non apparié |
| --- | ---: | ---: | ---: | ---: | --- |
| 600 | 916 | 896 | 895 | 21 | Titre du résumé |
| 601 | 1 331 | 1 309 | 1 309 | 22 | Aucun |
| 602 | 1 160 | 1 136 | 1 135 | 25 | Titre du résumé |
| 603 | 1 103 | 1 092 | 1 091 | 12 | Titre du résumé |
| 604 | 1 025 | 1 009 | 1 008 | 17 | Titre du résumé |

Les entrées allemandes sont les fichiers `OEBPS/Text/index_split_020.xhtml`, `042`, `064`, `086` et `090` respectivement. Le modèle local est LaBSE, instantané `836121a0533e5664b21c7aacc5d22951f2b8b25b`. Les blocs français analysés correspondent au commit `6a3b4681`, avant les corrections de ce lot. Empreintes SHA-256 des entrées allemandes brutes, dans le même ordre :

- 600 : `f46bb67aee7831a0eccdb06cc5ae1825a5402860a80b43b235b5110683c1c632`
- 601 : `c6b5df8b46b4118b978caf3178fdf903a6d1c5029023d8dcdb7cbe25bc0caa19`
- 602 : `fb0b57348e32ea652029d390aaf006d676070d98c2148fb58e607e045c049456`
- 603 : `fa97544f0d189428583cfaef213e17b4979b72fedc5c80938a5b816fc3aab84a`
- 604 : `fd82e44d7761cea08b2439e2ab59fb6bcda23a467ac60db361d56f15ad736ac8`

Un alignement, même à score élevé, ne prouve pas qu’une phrase à l’intérieur d’un paragraphe soit complète ou exacte. Ces cinq romans restent donc à vérifier, notamment pour la qualité du français et les omissions partielles. Dans le 600, quelques erreurs de français ont également été corrigées au début du texte.

Les résultats bruts provisoires se trouvent dans le dossier temporaire local `pr600-alignement.json` et `pr-align-601-604` ; les scripts du pilote sont `pr600_alignement.py` et `pr_align_601_604.py` dans ce même dossier. Ils ne sont pas des attestations de validation.

Un contrôle distinct des paragraphes composés uniquement d’un numéro suivi d’un point a comparé les 50 numéros de 600 à 649. Les listes concordent sauf pour le 644 : l’extraction allemande reconnaît les repères 1 puis 3 à 11, alors que le français ne reconnaissait que 1 avant correction. Le contrôle ciblé et ses limites sont précisés ci-dessous ; ce seul comptage ne prouve ni la présence ni l’absence de contenu narratif.

## Numéro 644 : contrôle structurel ciblé

L’alignement du fichier allemand `OEBPS/Text/index_split_076.xhtml` a permis de replacer les repères de section 3 à 11 et 16 séparateurs de scène, ainsi que deux répliques qui avaient été déplacées. Les repères numériques isolés concordent désormais avec ceux extraits de cet EPUB : 1 puis 3 à 11. Aucun repère isolé 2 n’a été trouvé dans le XHTML original ; ne pas en inventer sans autre preuve.

Certains paragraphes allemands sont coupés ou regroupés différemment du français et faussent l’alignement automatique. Le contrôle structurel n’établit pas la complétude ni la qualité globale. En particulier, un court dialogue français près de la section 8 ne se retrouve pas à la même place dans l’original consulté et reste à examiner.

## Anomalies encore à traiter

- La recherche initiale des termes « correction » ou « réponse précédente » signalait 51 numéros, avec des faux positifs dans les dialogues. Les formulations ciblées ci-dessus ont été traitées ; poursuivre la recherche d’autres consignes et examiner les occurrences dans leur contexte original.
- Les recherches de débuts de ligne allemands révèlent d’autres titres, phrases et fragments encore présents. Les noms propres, titres d’œuvres et termes fictifs exigent un tri contextuel.
- Établir la correspondance de chaque roman avec son EPUB, puis vérifier la structure et les portions de texte ; les rapports automatiques de taille, titres ou langue sont des indices, pas une preuve d’intégralité.
- Aucun des 1 950 numéros n’est encore attesté comme entièrement revu dans cette phase. Les corrections ci-dessus forment un premier lot ponctuel, et non une validation complète des romans concernés.

## Contrôles effectués

Les variantes explicites de marqueurs entre crochets ont été recherchées dans l’ensemble des fichiers ; de nouveaux types de marqueurs et consignes ont ensuite été trouvés. `git diff --check` a réussi après les corrections de ce lot. Les originaux et les fichiers préexistants non suivis doivent être préservés.
