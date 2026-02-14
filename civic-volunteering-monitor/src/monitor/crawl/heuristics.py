from __future__ import annotations

HEURISTIC_PATHS = [
    "/politikk",
    "/politikk-og-organisasjon",
    "/moter",
    "/moter-og-saker",
    "/saker",
    "/innsyn",
    "/postliste",
    "/aktuelt",
    "/nyheter",
    "/kunngjoringer",
    "/planer",
    "/planer-og-strategier",
    "/strategi",
    "/horing",
    "/dokumenter",
    "/rad-og-utvalg",
    "/frivillighet",
    "/frivilligsentral",
    "/tilskudd",
]

HIGH_RELEVANCE_KEYWORDS = [
    "frivillig", "frivillighet", "frivilligsentral", "sivilsamfunn",
    "samarbeid", "samspill", "partnerskap", "strategi", "plan", "politikk",
    "handlingsplan", "kartlegging", "oversikt", "foreningsregister", "foreningsportal",
    "tilskudd", "støtteordning", "medvirkning", "dialog", "plattformer", "ks",
]


def is_document_url(url: str) -> bool:
    lowered = url.lower().split("?")[0]
    return lowered.endswith(".pdf") or lowered.endswith(".docx") or lowered.endswith(".doc")


def is_high_relevance(text: str) -> bool:
    value = (text or "").lower()
    return any(k in value for k in HIGH_RELEVANCE_KEYWORDS)
