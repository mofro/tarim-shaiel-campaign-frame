// ===== FACTION INFLUENCE DATA =====
// Values represent relative influence on the Silk Road corridor (0-100 scale)
// Based on territorial control, military power, and trade dominance

const FACTIONS = [
  { id: 'han',       name: 'Han Dynasty',         color: '#c4443a' },
  { id: 'roman',     name: 'Roman / Byzantine',    color: '#6b5ba8' },
  { id: 'parthian',  name: 'Parthian Empire',      color: '#3a8a7c' },
  { id: 'kushan',    name: 'Kushan Empire',        color: '#d4915b' },
  { id: 'sassanid',  name: 'Sassanid Empire',      color: '#2e7d6e' },
  { id: 'turkic',    name: 'Turkic Khaganates',    color: '#7a9a5a' },
  { id: 'tang',      name: 'Tang Dynasty',         color: '#b84c4c' },
  { id: 'arab',      name: 'Arab Caliphates',      color: '#3d7a3d' },
  { id: 'tibetan',   name: 'Tibetan Empire',       color: '#8b6b3e' },
  { id: 'song',      name: 'Song Dynasty',         color: '#a85555' },
  { id: 'seljuk',    name: 'Seljuk / Khwarezmid',  color: '#4a8a6a' },
  { id: 'mongol',    name: 'Mongol Empire',        color: '#5b7fa5' },
];

// Sampled every ~25 years
const INFLUENCE_DATA = [
  { year: 1,    han: 30, roman: 22, parthian: 25, kushan: 8,  sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 25,   han: 32, roman: 25, parthian: 24, kushan: 12, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 50,   han: 28, roman: 26, parthian: 22, kushan: 18, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 75,   han: 30, roman: 25, parthian: 20, kushan: 22, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 100,  han: 32, roman: 28, parthian: 18, kushan: 25, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 125,  han: 28, roman: 30, parthian: 16, kushan: 24, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 150,  han: 22, roman: 28, parthian: 18, kushan: 26, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 175,  han: 16, roman: 24, parthian: 16, kushan: 24, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 200,  han: 10, roman: 20, parthian: 14, kushan: 22, sassanid: 0, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 225,  han: 4,  roman: 18, parthian: 4,  kushan: 20, sassanid: 18, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 250,  han: 2,  roman: 16, parthian: 0,  kushan: 18, sassanid: 24, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 275,  han: 0,  roman: 14, parthian: 0,  kushan: 14, sassanid: 28, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 300,  han: 0,  roman: 14, parthian: 0,  kushan: 10, sassanid: 30, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 325,  han: 0,  roman: 15, parthian: 0,  kushan: 8,  sassanid: 30, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 350,  han: 0,  roman: 14, parthian: 0,  kushan: 5,  sassanid: 32, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 375,  han: 0,  roman: 12, parthian: 0,  kushan: 2,  sassanid: 34, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 400,  han: 0,  roman: 10, parthian: 0,  kushan: 0,  sassanid: 35, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 425,  han: 0,  roman: 8,  parthian: 0,  kushan: 0,  sassanid: 34, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 450,  han: 0,  roman: 6,  parthian: 0,  kushan: 0,  sassanid: 34, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 475,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 32, turkic: 0, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 500,  han: 0,  roman: 8,  parthian: 0,  kushan: 0,  sassanid: 30, turkic: 4, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 525,  han: 0,  roman: 10, parthian: 0,  kushan: 0,  sassanid: 28, turkic: 8, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 550,  han: 0,  roman: 12, parthian: 0,  kushan: 0,  sassanid: 26, turkic: 18, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 575,  han: 0,  roman: 10, parthian: 0,  kushan: 0,  sassanid: 24, turkic: 22, tang: 0, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 600,  han: 0,  roman: 10, parthian: 0,  kushan: 0,  sassanid: 22, turkic: 20, tang: 4, arab: 0, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 625,  han: 0,  roman: 10, parthian: 0,  kushan: 0,  sassanid: 20, turkic: 16, tang: 16, arab: 4, tibetan: 2, song: 0, seljuk: 0, mongol: 0 },
  { year: 650,  han: 0,  roman: 8,  parthian: 0,  kushan: 0,  sassanid: 6,  turkic: 12, tang: 28, arab: 14, tibetan: 4, song: 0, seljuk: 0, mongol: 0 },
  { year: 675,  han: 0,  roman: 6,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 8,  tang: 24, arab: 22, tibetan: 10, song: 0, seljuk: 0, mongol: 0 },
  { year: 700,  han: 0,  roman: 6,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 6,  tang: 28, arab: 26, tibetan: 8, song: 0, seljuk: 0, mongol: 0 },
  { year: 725,  han: 0,  roman: 5,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 4,  tang: 30, arab: 28, tibetan: 10, song: 0, seljuk: 0, mongol: 0 },
  { year: 750,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 4,  tang: 22, arab: 32, tibetan: 12, song: 0, seljuk: 0, mongol: 0 },
  { year: 775,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 3,  tang: 14, arab: 36, tibetan: 10, song: 0, seljuk: 0, mongol: 0 },
  { year: 800,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 4,  tang: 12, arab: 38, tibetan: 8, song: 0, seljuk: 0, mongol: 0 },
  { year: 825,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 4,  tang: 10, arab: 38, tibetan: 6, song: 0, seljuk: 0, mongol: 0 },
  { year: 850,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 6,  tang: 8,  arab: 36, tibetan: 2, song: 0, seljuk: 0, mongol: 0 },
  { year: 875,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 8,  tang: 5,  arab: 34, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 900,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 10, tang: 3,  arab: 32, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 925,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 12, tang: 0,  arab: 30, tibetan: 0, song: 0, seljuk: 0, mongol: 0 },
  { year: 950,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 14, tang: 0,  arab: 28, tibetan: 0, song: 4, seljuk: 0, mongol: 0 },
  { year: 975,  han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 14, tang: 0,  arab: 26, tibetan: 0, song: 10, seljuk: 0, mongol: 0 },
  { year: 1000, han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 12, tang: 0,  arab: 24, tibetan: 0, song: 14, seljuk: 4, mongol: 0 },
  { year: 1025, han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 10, tang: 0,  arab: 20, tibetan: 0, song: 14, seljuk: 10, mongol: 0 },
  { year: 1050, han: 0,  roman: 4,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 6,  tang: 0,  arab: 16, tibetan: 0, song: 14, seljuk: 20, mongol: 0 },
  { year: 1075, han: 0,  roman: 3,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 4,  tang: 0,  arab: 14, tibetan: 0, song: 14, seljuk: 24, mongol: 0 },
  { year: 1100, han: 0,  roman: 3,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 3,  tang: 0,  arab: 12, tibetan: 0, song: 14, seljuk: 26, mongol: 0 },
  { year: 1125, han: 0,  roman: 3,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 2,  tang: 0,  arab: 10, tibetan: 0, song: 12, seljuk: 26, mongol: 0 },
  { year: 1150, han: 0,  roman: 3,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 2,  tang: 0,  arab: 10, tibetan: 0, song: 10, seljuk: 28, mongol: 0 },
  { year: 1175, han: 0,  roman: 3,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 2,  tang: 0,  arab: 10, tibetan: 0, song: 10, seljuk: 28, mongol: 0 },
  { year: 1200, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 2,  tang: 0,  arab: 10, tibetan: 0, song: 10, seljuk: 26, mongol: 6 },
  { year: 1210, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 2,  tang: 0,  arab: 10, tibetan: 0, song: 10, seljuk: 22, mongol: 14 },
  { year: 1225, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 0,  tang: 0,  arab: 8,  tibetan: 0, song: 8,  seljuk: 10, mongol: 30 },
  { year: 1250, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 0,  tang: 0,  arab: 4,  tibetan: 0, song: 6,  seljuk: 4,  mongol: 42 },
  { year: 1275, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 0,  tang: 0,  arab: 2,  tibetan: 0, song: 0,  seljuk: 2,  mongol: 52 },
  { year: 1300, han: 0,  roman: 2,  parthian: 0,  kushan: 0,  sassanid: 0,  turkic: 0,  tang: 0,  arab: 2,  tibetan: 0, song: 0,  seljuk: 2,  mongol: 50 },
];


// ===== TIMELINE EVENTS DATA =====
const EVENTS = [
  // 1st Century
  { year: 73,   title: "Ban Chao's Western Campaign",       type: "military",  desc: "Han general Ban Chao defeats the Xiongnu and secures the Tarim Basin, stabilizing the Silk Road's eastern corridor." },
  { year: 97,   title: "Gan Ying's Mission to Rome",        type: "trade",     desc: "Chinese envoy Gan Ying is dispatched toward Rome (Daqin) but turns back at the Persian Gulf, the closest China came to direct Roman contact." },
  { year: 100,  title: "Four Empires Stabilize the Road",   type: "political", desc: "The Roman, Parthian, Kushan, and Han empires simultaneously maintain order along their respective Silk Road segments — a rare era of pan-continental stability." },
  { year: 116,  title: "Trajan Reaches the Persian Gulf",   type: "military",  desc: "Roman Emperor Trajan's legions briefly conquer Mesopotamia and reach the Persian Gulf, the deepest Roman penetration into Parthian territory." },
  { year: 130,  title: "Han Retreat from Central Asia",     type: "political", desc: "The Han military withdraws from its westernmost positions, retreating to its traditional frontier and ceding control of Central Asian routes." },
  { year: 166,  title: "Roman Envoy Reaches China by Sea",  type: "trade",     desc: "A delegation claiming to represent Roman Emperor Marcus Aurelius arrives at the Han court via the maritime route through Southeast Asia." },

  // 2nd–3rd Century
  { year: 220,  title: "Fall of the Han Dynasty",           type: "political", desc: "The Han dynasty collapses, fragmenting China into the Three Kingdoms. Silk Road trade from the east declines sharply." },
  { year: 224,  title: "Sassanids Overthrow Parthians",     type: "military",  desc: "Ardashir I defeats the last Parthian king, founding the Sassanid Empire — which will dominate the central Silk Road for four centuries." },
  { year: 260,  title: "Shapur I Captures Emperor Valerian",type: "military",  desc: "Sassanid Emperor Shapur I captures Roman Emperor Valerian at the Battle of Edessa — a humiliation that reshapes the western Silk Road balance." },

  // 4th Century
  { year: 320,  title: "Gupta Empire Rises in India",       type: "political", desc: "The Gupta dynasty unifies much of India, facilitating maritime Silk Road trade through Indian Ocean routes." },
  { year: 330,  title: "Constantinople Founded",            type: "political", desc: "Emperor Constantine establishes Constantinople as the new Roman capital, shifting the empire's economic center eastward toward the Silk Road." },
  { year: 370,  title: "Huns Reach the Volga",              type: "military",  desc: "The Huns — possibly descended from the Xiongnu — arrive at the Volga River, beginning their devastating sweep across Europe." },
  { year: 395,  title: "Roman Empire Splits Permanently",   type: "political", desc: "The Roman Empire formally divides into Western and Eastern (Byzantine) halves, with Byzantium maintaining Silk Road connections." },

  // 5th–6th Century
  { year: 476,  title: "Fall of Western Rome",              type: "political", desc: "The Western Roman Empire falls to Germanic tribes. Byzantine Empire continues eastern trade, but European Silk Road demand collapses." },
  { year: 552,  title: "First Turkic Khaganate Founded",    type: "political", desc: "The Göktürks establish a vast steppe empire from Mongolia to the Black Sea, becoming major intermediaries on the Silk Road." },
  { year: 567,  title: "Turks and Byzantines Ally",         type: "trade",     desc: "The Turkic Khaganate and Byzantine Empire form an alliance to bypass Sassanid control of Silk Road trade." },

  // 7th Century
  { year: 618,  title: "Tang Dynasty Founded",              type: "political", desc: "The Tang dynasty begins in China, ushering in the Silk Road's golden age of cultural exchange and trade." },
  { year: 630,  title: "Tang Defeats Eastern Turks",        type: "military",  desc: "Emperor Taizong defeats the Eastern Turkic Khaganate, absorbing its people and extending Tang influence deep into Central Asia." },
  { year: 632,  title: "Arab Conquests Begin",              type: "military",  desc: "Following Muhammad's death, the Rashidun Caliphate launches rapid military expansion across the Middle East and Central Asia." },
  { year: 639,  title: "Tang Reopens the Silk Road",        type: "trade",     desc: "Tang military campaigns secure the western routes, reopening the Silk Road to an unprecedented volume of trade and cultural exchange." },
  { year: 651,  title: "Fall of the Sassanid Empire",       type: "military",  desc: "The last Sassanid emperor is killed as Arab armies complete their conquest of Persia, ending four centuries of Sassanid Silk Road dominance." },
  { year: 657,  title: "Tang Destroys Western Turks",       type: "military",  desc: "The Tang dynasty crushes the Western Turkic Khaganate, extending Chinese control to its farthest western point — the Pamirs." },
  { year: 678,  title: "Tibet Captures Silk Road Routes",   type: "military",  desc: "The expanding Tibetan Empire seizes control of key Silk Road passes, cutting off Tang access to Central Asia." },

  // 8th Century
  { year: 737,  title: "Tang Regains Silk Road Control",    type: "military",  desc: "After decades of Tibetan control, the Tang dynasty recaptures the Silk Road routes, beginning a second Pax Sinica and the road's golden age." },
  { year: 751,  title: "Battle of Talas",                   type: "military",  desc: "Abbasid Arab forces defeat the Tang army near the Talas River — the only direct Arab-Chinese battle. Ends Chinese westward expansion permanently." },
  { year: 755,  title: "An Lushan Rebellion",               type: "military",  desc: "A catastrophic rebellion devastates Tang China, killing millions and forcing the permanent withdrawal of Tang forces from Central Asia." },

  // 9th Century
  { year: 842,  title: "Tibetan Empire Collapses",          type: "political", desc: "The Tibetan Empire fragments after a succession crisis, removing a major power from the Silk Road's eastern section." },
  { year: 868,  title: "Samanid Dynasty in Transoxiana",    type: "political", desc: "The Persian Samanid dynasty rises in Central Asia, fostering a cultural renaissance and maintaining Silk Road trade under Islamic rule." },
  { year: 907,  title: "Fall of the Tang Dynasty",          type: "political", desc: "The Tang dynasty collapses into the chaotic Five Dynasties period, ending China's golden age of Silk Road engagement." },

  // 10th–11th Century
  { year: 960,  title: "Song Dynasty Founded",              type: "political", desc: "The Song dynasty reunifies much of China but faces persistent northern threats, shifting trade emphasis toward maritime routes." },
  { year: 1037, title: "Seljuk Empire Rises",               type: "political", desc: "Seljuk Turks establish dominance over Persia and Mesopotamia, controlling central Silk Road routes for nearly two centuries." },
  { year: 1071, title: "Battle of Manzikert",               type: "military",  desc: "Seljuk Turks crush the Byzantine army, capturing Emperor Romanos IV. Byzantium loses Anatolia and its role as a Silk Road gateway." },
  { year: 1095, title: "First Crusade Launched",            type: "military",  desc: "European Crusaders march east, creating new contact zones between Western Europe and the Islamic world along Silk Road termini." },

  // 12th–13th Century
  { year: 1141, title: "Battle of Qatwan",                  type: "military",  desc: "The Kara-Khitai defeat the Seljuks at Qatwan, shifting Central Asian power and inspiring European legends of Prester John." },
  { year: 1206, title: "Genghis Khan Unites the Mongols",   type: "political", desc: "Temüjin is proclaimed Genghis Khan, unifying the Mongol tribes and beginning the largest land empire in history." },
  { year: 1219, title: "Mongol Invasion of Khwarezmia",     type: "military",  desc: "Genghis Khan destroys the Khwarezmian Empire, razing Bukhara and Samarkand — devastating the Silk Road's richest cities." },
  { year: 1227, title: "Death of Genghis Khan",             type: "political", desc: "Genghis Khan dies, but his empire — stretching from Korea to Eastern Europe — is divided among his sons and continues expanding." },
  { year: 1241, title: "Mongols Invade Europe",             type: "military",  desc: "Mongol armies sweep through Russia, Poland, and Hungary, terrifying Christendom before withdrawing to settle succession." },
  { year: 1258, title: "Fall of Baghdad",                   type: "military",  desc: "Mongol forces under Hulagu sack Baghdad, killing the last Abbasid Caliph and ending five centuries of Islamic caliphal rule." },
  { year: 1271, title: "Kublai Khan Founds Yuan Dynasty",   type: "political", desc: "Kublai Khan establishes the Yuan dynasty in China, reuniting East and West under Mongol rule and reviving the Silk Road under the Pax Mongolica." },
  { year: 1275, title: "Marco Polo Arrives in China",       type: "trade",     desc: "Venetian merchant Marco Polo reaches Kublai Khan's court, beginning a 17-year stay that will introduce Europe to the riches of the East." },
  { year: 1295, title: "Ilkhanate Converts to Islam",       type: "political", desc: "The Mongol Ilkhanate in Persia formally converts to Islam, signing the Treaty of Aleppo with the Mamluks and reshaping western Silk Road politics." },
];
