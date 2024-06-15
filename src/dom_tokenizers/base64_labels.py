from enum import Enum, auto

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    KNOWN_WORD = auto()
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
)

KNOWN_LABELS = {}
for label, tokens in _KNOWN_LABELS:
    for token in tokens:
        KNOWN_LABELS[token] = label
