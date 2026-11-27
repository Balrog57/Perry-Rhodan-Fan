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

## Numéro 600 : premier contrôle du français

Un essai local de [LanguageTool](https://dev.languagetool.org/http-server), version 6.9-SNAPSHOT du 26 novembre 2026, a analysé le corps du texte en 23 blocs. L’archive utilisée porte le SHA-256 `5a183982e5b49abcabb5df301a6cfc2b9dea523b246564614ca33adc4a9f2e70` ; l’empreinte du corps avant les corrections ci-dessous est `89ab69c9261a04605aea7b04bac06887f716121d1508d803f1bc1edb7d33e405`. Le serveur était local et a été arrêté après utilisation.

L’outil a signalé 1 113 éléments, dont 906 vérifications orthographiques majoritairement liées à des noms et termes de l’univers. Après lecture ciblée, deux élisions, un accord, un résidu allemand et une formulation ont été corrigés. Les signalements restants, y compris les éventuelles erreurs que l’outil ne détecte pas, demandent encore un examen. Le résultat brut provisoire se trouve dans le dossier temporaire local `pr-languagetool-20261127/600.json` ; il ne constitue pas une validation du roman.

Le même outil a aussi analysé le 601 en 20 blocs (empreinte du corps : `9f45985bb5ffeb0da14290e2e626f7bbfd51dce3743a4d9394d08bebba8304ca`). Il a remonté 1 551 signalements, dont 1 387 orthographiques. Un tri ciblé des règles d’accord et d’élision examinées a surtout retrouvé des faux positifs sur les noms de vaisseaux ; il ne vaut pas relecture intégrale. Le résultat provisoire est `pr-languagetool-20261127/601.json` dans le dossier temporaire local.

## Lot 605–609 : alignement pilote

La même méthode locale et les mêmes limites s’appliquent. Les 90 séparateurs de scène allemands non appariés ont été replacés après contrôle des blocs voisins.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis | Autres écarts constatés |
| --- | ---: | ---: | ---: | ---: | --- |
| 605 | 1 177 | 1 155 | 1 154 | 23 | Titre français du résumé supplémentaire |
| 606 | 921 | 899 | 897 | 24 | Titre du résumé ; une réplique doublée, supprimée après comparaison |
| 607 | 1 441 | 1 423 | 1 422 | 18 | Titre allemand non apparié ; titre français réintroduit dans le corps |
| 608 | 1 297 | 1 279 | 1 278 | 19 | Titre français du résumé supplémentaire |
| 609 | 1 213 | 1 208 | 1 207 | 6 | Titre français du résumé supplémentaire |

Le titre allemand cité dans le résumé du 607 a aussi été traduit. Les résultats bruts provisoires et le script sont dans le dossier temporaire local `pr-align-605-609` et `pr_align_605_609.py`. Les fichiers français analysés correspondent au commit `a13a8644`, avant corrections. Les entrées allemandes `OEBPS/Text/index_split_092.xhtml`, `094`, `096`, `098` et `001` ont respectivement les empreintes SHA-256 suivantes :

- 605 : `555272f4cf22165b7f99c4896f0b42f642a148c071e18ad129a5fc7447bda6c6`
- 606 : `07e939ad80213404f7d6d8b59dd8e47fb8d47dc64c38c4d268c69f53fdf88d92`
- 607 : `ee300c5b5c78ac4ef5a8d4754f1729f7172771c3fe84165dc93ccb1f1d01d13e`
- 608 : `8499797aeb634f0383ad33942bb5ab1d7a6115bb3141bc72daee8a249500b02b`
- 609 : `13563eba2049deeed6dcc6bb212834062e7fe64fae07a1319f5f1c6040085167`

Ces statistiques ne prouvent pas que les paragraphes appariés soient complets ni que le français soit exempt d’erreurs ; les cinq romans restent à vérifier.

## Lot 610–614 : alignement pilote

La méthode et ses limites sont identiques aux lots précédents. Les séparateurs non appariés ont été replacés après contrôle des voisins ; les titres français des 611 et 614 ont été réintroduits au début des corps de texte.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis | Autres écarts constatés |
| --- | ---: | ---: | ---: | ---: | --- |
| 610 | 1 166 | 1 146 | 1 145 | 21 | Titre du résumé supplémentaire |
| 611 | 1 216 | 1 208 | 1 207 | 8 | Titre allemand non apparié ; titre français réintroduit |
| 612 | 1 260 | 1 235 | 1 234 | 26 | Titre du résumé supplémentaire |
| 613 | 1 009 | 987 | 986 | 23 | Titre du résumé supplémentaire |
| 614 | 1 433 | 1 413 | 1 412 | 20 | Titre allemand non apparié ; titre français réintroduit |

Les résultats provisoires et le script sont dans le dossier temporaire local `pr-align-610-614` et `pr_align_610_614.py`. Les fichiers français analysés correspondent au commit `a13a8644`, avant corrections. Les entrées allemandes `OEBPS/Text/index_split_002.xhtml`, `004`, `006`, `008` et `010` ont respectivement les empreintes SHA-256 suivantes :

- 610 : `b3e31d3e6d4b5e1ce729384c00d2cee9b30963ed7fcd141d7de55430c2af7bd0`
- 611 : `ff8e5e7b5216e51eb548e48dbe6ab9d82f850f691960b42cf865fdd542b08180`
- 612 : `cebe670f9c2cddba10e6f5f2c41f25af78d5a16b1069851ffddedd8e44bcc764`
- 613 : `04416a116b2b4273c10115e65cada97be649ff5fa6bf9d2f4caa7668ce2b0871`
- 614 : `14bdb9107ffe94b0ec12ba814978eda4272a04228ecb2ac435d8490186eeda3c`

Ces statistiques ne prouvent pas la complétude des paragraphes appariés ni la qualité globale du français ; les cinq romans restent à vérifier.

## Lot 615–619 : alignement pilote

Même méthode et mêmes limites que ci-dessus. Les séparateurs non appariés ont été replacés après contrôle des blocs voisins.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis |
| --- | ---: | ---: | ---: | ---: |
| 615 | 1443 | 1434 | 1433 | 9 |
| 616 | 1192 | 1184 | 1183 | 7 |
| 617 | 1212 | 1191 | 1190 | 22 |
| 618 | 1083 | 1072 | 1071 | 12 |
| 619 | 927 | 908 | 907 | 20 |

Le 615 contenait une fin de phrase allemande séparée mais déjà regroupée en français ; une ponctuation doublée et une formulation voisine ont été corrigées. Le 616 avait aussi une fin de phrase regroupée en français ; son titre a été ajouté au corps et le titre du résumé replacé avant le premier paragraphe du résumé. Dans les 617–619, les autres blocs français non appariés correspondent au titre du résumé.

Les résultats provisoires et le script sont dans le dossier temporaire local `pr-align-615-619` et `pr_align_615_619.py`. Les textes français correspondent au commit `40c9a322`, avant corrections. Empreintes SHA-256 des entrées allemandes brutes :

- 615 : `7b89ee18c46a52f8d113d635b369052e75128099e3d1dfae764d7574c8dea42c` (`OEBPS/Text/index_split_012.xhtml`)
- 616 : `5c97bb7970d1e537239a60dc4500b875743ad600c45797d8107287e8e72ed7cc` (`OEBPS/Text/index_split_014.xhtml`)
- 617 : `b1432ff09e3acea16763f43dce9f15e1b36c4e5a8b672fb24c6fcc16cf68e7a1` (`OEBPS/Text/index_split_016.xhtml`)
- 618 : `c36545ea74020413b961e2cdbe33de12d224914d4e9abd9e53b7ed677daeccc7` (`OEBPS/Text/index_split_018.xhtml`)
- 619 : `896f48208f1633bea1ff70904de0925b1a4874ab45697e02535c4c54e1b83210` (`OEBPS/Text/index_split_022.xhtml`)

Ces contrôles ne prouvent pas la complétude des paragraphes appariés ni la qualité globale du français ; ces cinq romans restent à vérifier.

## Lot 620–624 : alignement pilote

Même méthode et mêmes limites que ci-dessus. Les séparateurs non appariés ont été replacés après contrôle des blocs voisins. Pour chaque numéro, le seul bloc français non apparié était le titre du résumé.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis |
| --- | ---: | ---: | ---: | ---: |
| 620 | 1051 | 1035 | 1034 | 17 |
| 621 | 1149 | 1139 | 1138 | 11 |
| 622 | 1112 | 1101 | 1100 | 12 |
| 623 | 1290 | 1282 | 1281 | 9 |
| 624 | 1076 | 1065 | 1064 | 12 |

Les résultats provisoires et le script sont dans le dossier temporaire local `pr-align-620-624` et `pr_align_620_624.py`. Les textes français analysés correspondent au commit `9f12802f`, avant corrections. Empreintes SHA-256 des entrées allemandes brutes :

- 620 : `f6bb56fd48cbd7fd3beac5aae8b3f16db63498d5cb1fe86e53f73fc51f0fa237` (`OEBPS/Text/index_split_024.xhtml`)
- 621 : `86c090345ff875157a0ba1a6e9d4dc37ccce2206ccbe8c1ef30cbbcbea91197e` (`OEBPS/Text/index_split_026.xhtml`)
- 622 : `593674c8ec87784493088be7e676978fb1476cdb33f6443d5be0b1a561dc3a5a` (`OEBPS/Text/index_split_028.xhtml`)
- 623 : `93bc42fb14c6e14ae717679fb5353c4523255e0aa5a697139c73cc525949a568` (`OEBPS/Text/index_split_030.xhtml`)
- 624 : `0894f7ae3321a515ce2a31dac1db5850050665be72ca21982ad755f45217d470` (`OEBPS/Text/index_split_032.xhtml`)

Ces contrôles ne prouvent pas la complétude des paragraphes appariés ni la qualité globale du français ; ces cinq romans restent à vérifier.

## Lot 625–629 : alignement pilote

Même méthode et mêmes limites que ci-dessus. Les séparateurs non appariés ont été replacés après contrôle des blocs voisins. Pour chaque numéro, le seul bloc français non apparié était le titre du résumé.

| Numéro | Paragraphes DE | Blocs FR avant correction | Paires | Séparateurs rétablis |
| --- | ---: | ---: | ---: | ---: |
| 625 | 1194 | 1179 | 1178 | 16 |
| 626 | 876 | 848 | 847 | 29 |
| 627 | 1058 | 1048 | 1047 | 11 |
| 628 | 1343 | 1333 | 1332 | 11 |
| 629 | 1054 | 1047 | 1046 | 8 |

Les résultats provisoires et le script sont dans le dossier temporaire local `pr-align-625-629` et `pr_align_625_629.py`. Les textes français analysés correspondent au commit `c3d98431`, avant corrections. Empreintes SHA-256 des entrées allemandes brutes :

- 625 : `3a4a6d442d7e1a2378434b406b507f51d6fedbfe37bd372f6df170f04933e555` (`OEBPS/Text/index_split_034.xhtml`)
- 626 : `f5b8b7e3c935692678f68f56c71f477db4a13b5c1fc7de8fae5847133afc343d` (`OEBPS/Text/index_split_036.xhtml`)
- 627 : `b7e76277dca206f647d19bcdf3aa8c1e6f90d7be274dea0655b5ea14da204d8b` (`OEBPS/Text/index_split_038.xhtml`)
- 628 : `62e63e60a13b84c056f5c31ea0a844987e1b16540a7a7d50b2f42d174214b59f` (`OEBPS/Text/index_split_040.xhtml`)
- 629 : `ad20be64606ac4b81f098334b64cd3b296b678548bc7cca5bd46fdec1dbefe4c` (`OEBPS/Text/index_split_044.xhtml`)

Ces contrôles ne prouvent pas la complétude des paragraphes appariés ni la qualité globale du français ; ces cinq romans restent à vérifier.

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
