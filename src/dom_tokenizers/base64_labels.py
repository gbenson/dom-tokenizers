from enum import Enum, auto

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    KNOWN_WORD = auto()
    DELIMITED_WORDS = auto()
    CAMELCASE = auto()
    NOT_BASE64 = auto()
    BASE64_ENCODED_GIF = auto()
    BASE64_ENCODED_JPEG = auto()
    BASE64_ENCODED_PNG = auto()
    BASE64_ENCODED_SVG = auto()
    BASE64_ENCODED_WEBP = auto()
    BASE64_ENCODED_WOFF = auto()
    BASE64_ENCODED_DATA = auto()
    BASE64_ENCODED_UTF8 = auto()
    BASE64_ENCODED_JSON_SANDWICH = auto()
    UNLABELLED = auto()

_KNOWN_LABELS = (
    (Label.BASE64_ENCODED_DATA,
     ("FeW97", "ILbm6", "SuDo6", "fIaT0", "hoT41", "iCE40", "iDs10",
      "iP134", "jUg81", "loN59", "rOsa2", "raPE0", "sO875", "sOd04",
      "sTAp9", "uP492")),
    (Label.BASE64_ENCODED_DATA,
     ("AfDOScZbxtRV", "DcPeMOEKNeEPoO", "I5FlojXOfTI6", "U2Uzur1TI5I",
      "dfFtcTIAuri06", "iTNHywi", "xWRBJ07MtEV")),
    (Label.NOT_BASE64,
     ("AlPark", "BTFvert", "CharonPlutoIKEv1", "EVCharging", "EVHaste",
      "FuturaBT", "HaxeFoundation", "HaxeManual", "HaxeOrg", "paramBp",
      "KonamiSCCI", "SCCIAudio", "SCCIExpansion", "SecuShare","SnellBT",
      "SmartCardsIKEv2", "SuperNETs", "TIGrund", "TNReady", "TNStats",
      "TNTracker", "ToutFocus", "aThisBP", "bpLogEvent", "setSCCIMode",
      "bpSmall", "evName", "marginTN", "paddingAL", "toutInnerWrapper",
      "paddingBT", "HaxeTarget", "paddingTN", "scciMode","startInSCCI",
      "scciSelected", "bpRegType", "tiActions", "tiDirs", "iconArbi")),
    (Label.BASE64_ENCODED_DATA,
     ("A6Mspp5", "A7Uria", "A8Kawo", "A9WFUN", "ADALubz", "AIdro",
      "AKTAAd", "AOn4CLBlodALrMO4", "AOn4CLCgArkb", "AOn4CLDC", "BlfdI",
      "AfDwksN", "AOrYGslmCC", "APiow8B9", "ASipiYPm", "AXTA3RCh",
      "AfDOScZbxtRV", "AiGifuK", "B5WDBR47LC", "BE2SMphg", "BI5Smsp",
      "BeWWFK", "BpomA", "BtBujjiN", "C2AS9TDMEMy", "CAnGagg", "FELoce",
      "CR9TITNA", "CeMt3Rozb", "Ch8ONAH", "ChMKnwq", "ChMOzATNRInt",
      "CjxkReA", "ClMOSP3", "CmCApwr", "ConnDoi", "CovoM1F7AANc4A",
      "CrCLCmml", "CrXRowo", "CsivClMO", "CssKqEMKjwp", "CtMOQED",
      "CtUMaAsKjacO", "CtsKhwo", "DcPeMOEKNeEPoO", "DiMOIX8K", "DimkCe",
      "DiMOIwonDoV", "DngrPc", "DoBTDgMOPES", "EDaTany", "EKusdA",
      "EnisIf", "EpamAfA2", "EuWBKISdH", "ExSIRKFn", "F0CKYS2PR6",
      "F5HOSM18IlWAAB", "FEYI4PA", "FShvaI", "FZFVAd", "Fech7TI",
      "FlKISH", "G4ReAufh", "GaaboA", "GbfeNm", "Ggcx0LB", "H2WwyoEU84",
      "H7UrgeI7", "HBherRA", "HPoGAAC", "Hpue7I", "HrDsfsU", "I0PpkiI",
      "HrNOFbJtregEWAuP7", "I53BINI7", "I5FlojXOfTI6", "I7Folf",
      "I9Jtec", "IBADCc", "IBHSScD4", "IWkxwApX", "IfEcue", "InKIFF",
      "InubPp", "JrDynuMsF79EM", "KJWLUk", "KMONRsK", "KZNZ7SN4",
      "Karm5AT", "Kmre1I", "Kndd0A", "LN9XdvdIPmdyX0AM", "LRRISw",
      "LSVrad", "LiezSn", "LsNahb", "M5AfBuke", "MUEM7Up", "NIHltu8",
      "NWbciBaku", "NbnmF20Ex", "NtWfybM3", "OLJA28Nc", "OTImsiBi3Nj",
      "OhScic", "OrrEGGI", "OsKLOG", "OutyUnpfHIaeaSr2B", "PR65KTRS",
      "ParxURI7", "PnnvFnOh", "PoSukl", "QUSS7FT", "RFLpLEOW7MPH",
      "SATNMc", "SEPemc", "SagzRs", "SpIjsi7K1", "TUHYKit", "TcccNw",
      "U2Uzur1TI5I", "UMOS7LECT9E", "UNPdcd", "UbgaA", "UsykStE",
      "UzumSc", "Va2GNiava", "WgchCsV", "Wjsb0VBr", "WqmrI", "XxIgdb",
      "YRMmle", "ZboroQ", "ZirikUp0PcMK0", "ZunoMS76M4", "a3IWST6",
      "a8FEIO", "a8FENfgsAUQt", "aCOnZADJ9SaP", "aLYTO", "aOtTafta5",
      "abITKI", "adpi9LbJjiaI", "aeiu09I96", "aizuI7", "akfgAsXPosY2",
      "aomaEc", "apKMcifNC", "awnedC", "bCccan", "bSU5KUTU", "bUnraFF6",
      "bcFySARGE", "beVlab", "bevkHo", "biabiR", "bobjEGHK", "brKmxb",
      "brMEAE", "cAb5ISMA8", "cAktiA", "cbrkYRShN", "cfbgIi", "chKlql",
      "chchrT", "cjjjGSw", "cmAPIB", "cpfrOh", "ctHpde", "ctMRrea6",
      "cyubVe", "dWjzoA", "dWlnoI", "dbTOUD", "dfFtcTIAuri06", "flrnKG",
      "djewMgco", "dohlPp", "dosaNO", "drogAu", "duRjpb", "duclA",
      "ecKwpn56F", "enTSAE", "esZGSZ", "fAWaez", "fBEVsPaCp8VIGONor",
      "fBaCAPON", "ftWfoy", "gSACQWmkb", "gWthkA", "ghinId", "goKHTC",
      "golbyW", "gubaDc", "guyjGr", "haAclf", "haINNO", "hesxLdBcOIMS",
      "hfdfGO", "hiCibw", "huculX", "hwehI", "i0AgtrO", "i3Plnc",
      "iInmeY", "iKEjhl", "iLChyz", "iLLAM7", "iMFuat", "iNzefM",
      "iPJokm97", "iPrmlT", "iSazde", "iTNHywi", "idutPp", "iierOPJo",
      "ijsaAL", "iltoET", "imWYAI", "inaeDb", "irWGOL", "isOjlu",
      "isPrew", "itGidr", "ixWXTX", "jaKCJRDiE", "jeafCt", "jhobRf",
      "jofiAf", "jsDSRA", "jsIPcnb", "kFzknKm", "kUrl3NHIS", "kaiyOsP",
      "kbznRf", "keppNg", "kgPACF", "khleEm", "kijlA", "kjcrBg",
      "kkrdEu", "kmR00IAslkAn08C", "kojmCrnaG", "kqvtDulzUYmasY1",
      "kstqJO", "ktxcLB", "kuinIX", "kuorLA", "lPUPY9A", "lSENTMo",
      "laNcwc", "ldrrSp", "ldwaSC", "leowGeo8", "loQpcr", "lsCCHocuE",
      "meDrgwQ", "meemDO8", "mianAm", "mrJRlmb", "mrSlsb", "msStPpmt",
      "mt4WMWD", "n04OP14KGFefy", "nVKaoxLsANov", "nmIDLC", "oIgno5Fb",
      "oNsUTIA", "okOzalK4", "olWAIP", "olXuIEzccSU", "ozDibt",
      "p71FirUNDI", "p7OPMrpp", "ph6RtagF", "prAHAB", "ptDaswOsUhRe",
      "pxOdidU", "qWaare", "qWwhp43A", "r6MeHogsA", "rNsKUNJ", "tsQazb",
      "rOrgeGO", "sCtimFl", "sEqCyda", "sTcTpog", "seVajd", "spAWmym",
      "tCl8WQBZ", "tWmBOLL", "tnal1A", "toldZObfw", "troi7CE", "wHaque",
      "uohcLN9Y", "vNo0Weih8", "viPire", "wAlluCc", "wDeor9A", "walmI",
      "wHopahPt", "wgxiMe", "wiO4BI90PrblA", "wogfNg", "wpcmRD",
      "x4NSLoJkrv", "xAloxTHCB", "xBbsrc", "xWRBJ07MtEV", "xhov2SaS1ME",
      "yMeBRBY", "zoicIX")),
)

KNOWN_LABELS = {}
for label, tokens in _KNOWN_LABELS:
    for token in tokens:
        KNOWN_LABELS[token] = label
