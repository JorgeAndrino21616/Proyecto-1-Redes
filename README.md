Se necesita tener una API Key de Groq, se le tiene que agregar a groq.py y llm_client.py antes de correr host.py

Ejemplo de funcionamiento:

=== League of Legends Champion Builder ===
Your champion: Gnar
Characteristic: AP
Enter 5 enemy champions separated by commas: Gnar, Aatrox, Garen, Darius, Riven

Fetching static data from DDragon...
{'ok': True, 'version': '15.17.1', 'lang': 'en_US'}
Setting up the matchup...
{'ok': True, 'matchup': {'ally_champion': 'gnar', 'ally_characteristic': 'AP', 'enemy_team': ['gnar', 'aatrox', 'garen', 'darius', 'riven']}}
Analyzing enemy composition...
{'mix': {'ad_pct': 100, 'ap_pct': 0}, 'tanks': 3, 'cc': 'none', 'healing': 'none', 'crit_threat': 'high', 'poke': 'medium'}
Suggested RUNES:
{'primary_tree': 'Domination', 'keystone': 'Electrocute', 'primary': ['Taste of Blood', 'Eyeball Collection', 'Ultimate Hunter'], 'secondary_tree': 'Sorcery', 'secondary': ['Manaflow Band', 'Transcendence'], 'statShards': ['Adaptive', 'Adaptive', 'Armor'], 'why': ['AP burst/skirmish profile', 'Armor shard vs AD']}
Suggested SUMMONER SPELLS:
{'summoners': ['Flash', 'Teleport'], 'alt': ['Flash', 'Barrier'], 'why': 'AP: TP for tempo/roams; Barrier into strong burst comps.'}
Suggested ITEMS:
{'starter': ["Doran's Ring", 'Health Potion'], 'boots': {'pick': "Sorcerer's Shoes", 'alt': "Mercury's Treads", 'rule': 'Penetration for damage; Mercs vs heavy CC/AP.'}, 'core': [{'item': "Luden's Companion", 'why': 'Burst + mana efficiency for poke/pick.'}, {'item': 'Shadowflame', 'why': 'Great vs shields; flat pen spike.'}, {'item': "Zhonya's Hourglass", 'why': 'Defensive active vs engage/burst.'}], 'situational': [{'item': "Banshee's Veil", 'when': 'Pick-heavy or magic burst threats.'}, {'item': "Rabadon's Deathcap", 'when': 'Snowball/late scaling power spike.'}, {'item': 'Void Staff', 'when': 'Enemy stacking MR.'}]}
