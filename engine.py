"""Grain — local multi-pass text humanizer engine."""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# 1. AI-tell demolition
# ---------------------------------------------------------------------------

# (pattern, replacement) — case-insensitive; replacement may be callable(match)
# Prefer empty string or natural phrasing over stilted synonyms.

AI_PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    # --- Priority multi-word (before single-word swaps) ---
    (r"\bplays?\s+a\s+crucial\s+role\b", "matters a lot"),
    (r"\bplayed\s+a\s+crucial\s+role\b", "mattered a lot"),
    (r"\bplaying\s+a\s+crucial\s+role\b", "mattering a lot"),
    (r"\bplays?\s+a\s+(?:key|vital|significant)\s+role\b", "matters"),
    (r"\bnavigat(?:e|es|ed|ing)\s+the\s+realm\s+of\b", "deal with"),
    (r"\bnavigat(?:e|es|ed|ing)\s+the\b", "deal with"),
    (r"\bin the realm of\b", "in"),
    (r"\brealm of\b", ""),
    (r"\bwhen it comes to unlocking\b", "to unlock"),
    (r"\bwhen it comes to\b", "for"),
    (r"\bin today'?s world,?\s*", ""),
    (r"\bit is important to note that\b", ""),
    (r"\bdigital landscape\b", "online world"),
    (r"\bseamless journey\b", "smooth path"),
    (r"\bfostering a\b", "building a"),
    (r"\ba myriad of\b", "many"),
    # Classic AIisms
    (r"\bdelving into\b", "looking into"),
    (r"\bdelve(?:s|d)?\s+into\b", "look into"),
    (r"\bdelve(?:s|d|ing)?\b", "dig into"),
    (r"\btapestry\b", "mix"),
    (r"\brichtapestry\b", "rich mix"),
    (r"\bin the (?:ever[- ]changing |broader |complex )?landscape of\b", "in"),
    (r"\bdigital landscape\b", "online world"),
    (r"\btechnological landscape\b", "tech world"),
    (r"\bcompetitive landscape\b", "competition"),
    (r"\bin the realm of\b", "in"),
    (r"\brealm of\b", "world of"),
    (r"\bembarking on\b", "starting"),
    (r"\bembark(?:s|ed)?\s+on\b", "start"),
    (r"\bembark(?:s|ed|ing)?\b", "begin"),
    (r"\bpivotal\b", "key"),
    (r"\bcrucial\b", "important"),
    (r"\bunderscore(?:s|d|ing)?\b", "highlight"),
    (r"\bshowcasing\b", "showing"),
    (r"\bshowcase(?:s|d)?\b", "show"),
    (r"\bleveraging\b", "using"),
    (r"\bleverage(?:s|d)?\b", "use"),
    (r"\butilizing\b", "using"),
    (r"\butilize(?:s|d)?\b", "use"),
    (r"\butilisation\b", "use"),
    (r"\butilization\b", "use"),
    (r"\bcommencing\b", "starting"),
    (r"\bcommence(?:s|d)?\b", "start"),
    (r"\bfacilitating\b", "helping"),
    (r"\bfacilitate(?:s|d)?\b", "help"),
    (r"\brobust\b", "solid"),
    (r"\bseamless(?:ly)?\b", "smooth"),
    (r"\bcutting[- ]edge\b", "modern"),
    (r"\bgroundbreaking\b", "new"),
    (r"\bstate[- ]of[- ]the[- ]art\b", "up-to-date"),
    (r"\bfurthermore,?\s*", ""),
    (r"\bmoreover,?\s*", ""),
    (r"\badditionally,?\s*", "Also, "),
    (r"\bin conclusion,?\s*", ""),
    (r"\bto summarize,?\s*", ""),
    (r"\bin summary,?\s*", ""),
    (r"\bit is important to note that\b", ""),
    (r"\bit'?s important to note that\b", ""),
    (r"\bit is worth noting that\b", ""),
    (r"\bwhen it comes to\b", "with"),
    (r"\bin today'?s world,?\s*", ""),
    (r"\bin today'?s (?:fast[- ]paced |digital )?age,?\s*", ""),
    (r"\bin this day and age,?\s*", ""),
    (r"\bplays\s+a\s+crucial\s+role\b", "matters a lot"),
    (r"\bplay\s+a\s+crucial\s+role\b", "matter a lot"),
    (r"\bplayed\s+a\s+crucial\s+role\b", "mattered a lot"),
    (r"\bplaying\s+a\s+crucial\s+role\b", "mattering a lot"),
    (r"\bplays\s+a\s+(?:key|vital|significant)\s+role\b", "matters"),
    (r"\bplay\s+a\s+(?:key|vital|significant)\s+role\b", "matter"),
    (r"\bplayed\s+a\s+(?:key|vital|significant)\s+role\b", "mattered"),
    (r"\bplaying\s+a\s+(?:key|vital|significant)\s+role\b", "mattering"),
    (r"\ba myriad of\b", "many"),
    (r"\bmyriad\b", "many"),
    (r"\bnestled\b", "set"),
    (r"\bvibrant\b", "lively"),
    (r"\ba testament to\b", "proof of"),
    (r"\btestament to\b", "proof of"),
    (r"\bfostering\b", "building"),
    (r"\bfoster(?:s|ed)?\b", "encourage"),
    (r"\benhancing\b", "improving"),
    (r"\benhance(?:s|ed)?\b", "improve"),
    (r"\bunlocking the\b", "opening up the"),
    (r"\bunlock(?:s|ed)? the\b", "open up the"),
    (r"\bunlock(?:s|ed)? potential\b", "tap potential"),
    (r"\bempowering\b", "helping"),
    (r"\bempower(?:s|ed)?\b", "help"),
    (r"\bnavigat(?:e|es|ed|ing) the\b", "deal with"),
    (r"\bthe world of\b", ""),
    (r"\bin the world of\b", "in"),
    (r"\bnot only\s+(.+?)\s+but also\b", r"\1 and also"),
    (r"\bat its core,?\s*", ""),
    (r"\bat the end of the day,?\s*", ""),
    (r"\bin a nutshell,?\s*", ""),
    (r"\blet'?s dive in\.?\s*", ""),
    (r"\blet'?s dig deeper\.?\s*", ""),
    (r"\bwithout further ado,?\s*", ""),
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bin the event that\b", "if"),
    (r"\ba wide range of\b", "many"),
    (r"\ba plethora of\b", "lots of"),
    (r"\bplethora of\b", "lots of"),
    (r"\bholistic\b", "full"),
    (r"\bparadigm\b", "model"),
    (r"\bsynerg(?:y|ies|istic)\b", "teamwork"),
    (r"\bgame[- ]changer\b", "big shift"),
    (r"\brevolutionary\b", "major"),
    (r"\btransformative\b", "big"),
    (r"\binnovative\b", "new"),
    (r"\bunderscores the importance of\b", "shows why"),
    (r"\bit goes without saying that\b", ""),
    (r"\bneedless to say,?\s*", ""),
    (r"\bin light of\b", "given"),
    (r"\bwith that being said,?\s*", "Still, "),
    (r"\bthat being said,?\s*", "Still, "),
    (r"\bon the other hand,?\s*", "Then again, "),
    (r"\bas previously mentioned,?\s*", ""),
    (r"\bas mentioned (?:earlier|above),?\s*", ""),
    (r"\bit should be noted that\b", ""),
    (r"\bone might argue that\b", "some say "),
    (r"\bin essence,?\s*", ""),
    (r"\bessentially,?\s*", ""),
    (r"\bfundamentally,?\s*", ""),
    (r"\bultimately,?\s*", ""),
    (r"\bsignificantly\b", "a lot"),
    (r"\bcomprehensive(?:ly)?\b", "thorough"),
    (r"\bmeticulous(?:ly)?\b", "careful"),
    (r"\bintricate\b", "detailed"),
    (r"\bnuanced\b", "subtle"),
    (r"\bmultifaceted\b", "varied"),
    (r"\bdeep dive\b", "closer look"),
    (r"\bdeep-dive\b", "closer look"),
    (r"\bunpacking\b", "breaking down"),
    (r"\bunpack(?:s|ed)?\b", "break down"),
    (r"\bshed(?:s|ding)? light on\b", "explain"),
    (r"\bpave(?:s|d|ing)? the way\b", "open the door"),
    (r"\bat the forefront of\b", "leading in"),
    (r"\bin an era of\b", "in a time of"),
    (r"\bever[- ]evolving\b", "changing"),
    (r"\bbeacon of\b", "sign of"),
    (r"\bcornerstone of\b", "basis of"),
    (r"\bin this landscape\b", "here"),
    (r"\bthis landscape\b", "this field"),
    (r"\bharnessing\b", "using"),
    (r"\bharness(?:es|ed)?\b", "use"),
    (r"\bstreamlining\b", "simplifying"),
    (r"\bstreamline(?:s|d)?\b", "simplify"),
    (r"\boptimizing\b", "improving"),
    (r"\boptimize(?:s|d)?\b", "improve"),
    (r"\boptimising\b", "improving"),
    (r"\boptimise(?:s|d)?\b", "improve"),
    (r"\bendeavor(?:s)?\b", "effort"),
    (r"\bendeavour(?:s)?\b", "effort"),
    (r"\baspirations\b", "goals"),
    (r"\b(?:your|our|the) journey\b", "the process"),
    (r"\bseamless journey\b", "smooth path"),
    (r"\binvaluable\b", "really useful"),
    (r"\bunparalleled\b", "rare"),
    (r"\brealm\b", "area"),
    (r"\btestament\b", "proof"),
    (r"\bbolstering\b", "strengthening"),
    (r"\bbolster(?:s|ed)?\b", "strengthen"),
    (r"\bcatalyst for\b", "push for"),
    (r"\binterplay between\b", "link between"),
    (r"\bintricacies of\b", "details of"),
    (r"\bwoven into the fabric\b", "part of"),
    (r"\bfabric of\b", "core of"),
    (r"\ba testament\b", "proof"),
    (r"\bstands as a\b", "is a"),
    (r"\bserves as a\b", "is a"),
    (r"\bacts as a\b", "is a"),
    (r"\bin today'?s digital age,?\s*", ""),
    (r"\bto put it simply,?\s*", ""),
    (r"\bsuffice it to say,?\s*", ""),
    (r"\bit is essential to\b", "you should"),
    (r"\bit is imperative to\b", "you need to"),
    (r"\ba key takeaway\b", "the main point"),
    (r"\bkey takeaways\b", "main points"),
    (r"\blet'?s explore\b", "here's"),
    (r"\blet us explore\b", "here is"),
    (r"\bwe will explore\b", "we cover"),
    (r"\bthis article (?:will|aims to)\b", "this piece"),
    (r"\bin this (?:blog )?post,?\s*(?:we will|we'?ll)?\s*", ""),
    (r"\brest assured,?\s*", ""),
    (r"\bbe sure to\b", ""),
    (r"\bmake sure to\b", ""),
    (r"\bfeel free to\b", ""),
    (r"\bat your fingertips\b", "ready to use"),
    (r"\bgame changing\b", "big"),
    (r"\bnext[- ]level\b", "better"),
    (r"\bbest[- ]in[- ]class\b", "top"),
    (r"\bworld[- ]class\b", "excellent"),
    (r"\bmission[- ]critical\b", "critical"),
    (r"\bend[- ]to[- ]end\b", "full"),
    (r"\bactionable insights\b", "useful takeaways"),
    (r"\bactionable\b", "practical"),
    (r"\bdrive(?:s|d|ing)?\s+(?:meaningful\s+)?impact\b", "make a difference"),
    (r"\bmove the needle\b", "make real progress"),
    (r"\blow[- ]hanging fruit\b", "easy wins"),
    (r"\bcircle back\b", "follow up"),
    (r"\btouch base\b", "check in"),
    (r"\bsynergize\b", "work together"),
    (r"\bideate\b", "brainstorm"),
    (r"\bonboarding experience\b", "getting started"),
    (r"\buser[- ]centric\b", "user-focused"),
    (r"\bdata[- ]driven\b", "based on data"),
    (r"\bholistically\b", "as a whole"),
    (r"\bproactively\b", "ahead of time"),
    (r"\bgo[- ]to\b", "usual"),
    (r"\binvaluable insights\b", "useful ideas"),
    (r"\bvaluable insights\b", "useful ideas"),
    (r"\bgain insights\b", "learn"),
    (r"\bglean insights\b", "learn"),
    (r"\bbring to the table\b", "offer"),
    (r"\bat the intersection of\b", "between"),
    (r"\bin today'?s competitive (?:market|environment),?\s*", ""),
    (r"\bas we navigate\b", "as we deal with"),
    (r"\bas businesses navigate\b", "as businesses face"),
    (r"\bthe importance of\b", ""),
    (r"\bcannot be overstated\b", "really matters"),
    (r"\bcan'?t be overstated\b", "really matters"),
    (r"\bin a meaningful way\b", "for real"),
    (r"\bin a significant manner\b", "a lot"),
    (r"\bhas the potential to\b", "could"),
    (r"\bpossesses the ability to\b", "can"),
    (r"\bin close proximity to\b", "near"),
    (r"\bprior to\b", "before"),
    (r"\bsubsequent to\b", "after"),
    (r"\bin spite of the fact that\b", "even though"),
    (r"\bwith regard to\b", "about"),
    (r"\bwith respect to\b", "about"),
    (r"\bin terms of\b", "for"),
    (r"\bthe fact that\b", "that"),
    (r"\bit is clear that\b", ""),
    (r"\bclearly,?\s*", ""),
    (r"\bobviously,?\s*", ""),
    (r"\bof course,?\s*", ""),
    (r"\bcertainly,?\s*", ""),
    (r"\bundoubtedly,?\s*", ""),
    (r"\bindubitably,?\s*", ""),
]

CONTRACTIONS: list[tuple[str, str]] = [
    (r"\bit is\b", "it's"),
    (r"\bIt is\b", "It's"),
    (r"\bthat is\b", "that's"),
    (r"\bThat is\b", "That's"),
    (r"\bthere is\b", "there's"),
    (r"\bThere is\b", "There's"),
    (r"\bthere are\b", "there're"),
    (r"\bwhat is\b", "what's"),
    (r"\bWhat is\b", "What's"),
    (r"\bwho is\b", "who's"),
    (r"\bdo not\b", "don't"),
    (r"\bDo not\b", "Don't"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bDoes not\b", "Doesn't"),
    (r"\bdid not\b", "didn't"),
    (r"\bDid not\b", "Didn't"),
    (r"\bis not\b", "isn't"),
    (r"\bIs not\b", "Isn't"),
    (r"\bare not\b", "aren't"),
    (r"\bAre not\b", "Aren't"),
    (r"\bwas not\b", "wasn't"),
    (r"\bWas not\b", "Wasn't"),
    (r"\bwere not\b", "weren't"),
    (r"\bwill not\b", "won't"),
    (r"\bWill not\b", "Won't"),
    (r"\bwould not\b", "wouldn't"),
    (r"\bcould not\b", "couldn't"),
    (r"\bshould not\b", "shouldn't"),
    (r"\bcannot\b", "can't"),
    (r"\bCannot\b", "Can't"),
    (r"\bcan not\b", "can't"),
    (r"\bhave not\b", "haven't"),
    (r"\bhas not\b", "hasn't"),
    (r"\bhad not\b", "hadn't"),
    (r"\bI am\b", "I'm"),
    (r"\byou are\b", "you're"),
    (r"\bYou are\b", "You're"),
    (r"\bwe are\b", "we're"),
    (r"\bWe are\b", "We're"),
    (r"\bthey are\b", "they're"),
    (r"\bThey are\b", "They're"),
    (r"\bI will\b", "I'll"),
    (r"\byou will\b", "you'll"),
    (r"\bwe will\b", "we'll"),
    (r"\bthey will\b", "they'll"),
    (r"\bI have\b", "I've"),
    (r"\byou have\b", "you've"),
    (r"\bwe have\b", "we've"),
    (r"\bthey have\b", "they've"),
    (r"\blet us\b", "let's"),
    (r"\bLet us\b", "Let's"),
]

# Soften absolute claims
ABSOLUTE_SOFTENERS: list[tuple[str, str]] = [
    (r"\balways\b", "usually"),
    (r"\bnever\b", "rarely"),
    (r"\beveryone knows\b", "plenty of people know"),
    (r"\beveryone\b", "most people"),
    (r"\bnobody\b", "few people"),
    (r"\bguarantees?\b", "helps"),
    (r"\bperfect(?:ly)?\b", "strong"),
    (r"\bthe best\b", "a strong"),
    (r"\bthe only\b", "a clear"),
    (r"\bmust\b", "should"),
    (r"\bcrucial that\b", "important that"),
]

# Light synonym / paraphrase pairs (word-level, meaning-preserving)
SYNONYM_SWAPS: list[tuple[str, list[str]]] = [
    (r"\bhowever\b", ["still", "but", "even so"]),
    (r"\btherefore\b", ["so", "that's why", "which means"]),
    (r"\bthus\b", ["so", "and so"]),
    (r"\bhence\b", ["so"]),
    (r"\bapproximately\b", ["about", "roughly"]),
    (r"\bnumerous\b", ["many", "plenty of"]),
    (r"\bvarious\b", ["different", "a few different"]),
    (r"\bassist\b", ["help"]),
    (r"\bobtain\b", ["get"]),
    (r"\bpurchase\b", ["buy"]),
    (r"\brequire\b", ["need"]),
    (r"\brequires\b", ["needs"]),
    (r"\bdemonstrate\b", ["show"]),
    (r"\bdemonstrates\b", ["shows"]),
    (r"\bindicate\b", ["point to", "suggest"]),
    (r"\bindicates\b", ["points to", "suggests"]),
    (r"\bprovide\b", ["give", "offer"]),
    (r"\bprovides\b", ["gives", "offers"]),
    (r"\bregarding\b", ["about", "on"]),
    (r"\bconcerning\b", ["about"]),
    (r"\bcurrently\b", ["now", "right now"]),
    (r"\bpreviously\b", ["before", "earlier"]),
    (r"\bsubsequently\b", ["later", "then"]),
    (r"\bimmediately\b", ["right away", "at once"]),
    (r"\bfrequently\b", ["often"]),
    (r"\boccasionally\b", ["now and then"]),
    (r"\battempt\b", ["try"]),
    (r"\battempts\b", ["tries"]),
    (r"\bindividuals\b", ["people"]),
    (r"\bindividual\b", ["person"]),
    (r"\butilize\b", ["use"]),
    (r"\bmethod\b", ["way", "approach"]),
    (r"\bmethods\b", ["ways", "approaches"]),
    (r"\badvantage\b", ["upside", "plus"]),
    (r"\bdisadvantage\b", ["downside", "drawback"]),
    (r"\bimportant\b", ["big", "key", "worth noting"]),
    (r"\bsignificant\b", ["real", "notable", "serious"]),
]

MODE_PROFILES = {
    "casual": {
        "contractions": True,
        "fragments_ok": True,
        "soften": True,
        "start_and_but": True,
        "formality": 0,
    },
    "professional": {
        "contractions": True,
        "fragments_ok": False,
        "soften": True,
        "start_and_but": False,
        "formality": 1,
    },
    "academic-light": {
        "contractions": False,
        "fragments_ok": False,
        "soften": True,
        "start_and_but": False,
        "formality": 2,
    },
}


@dataclass
class HumanizeResult:
    output: str
    changes: list[str] = field(default_factory=list)


def _apply_replacements(
    text: str,
    pairs: list[tuple[str, str]],
    flags: int = re.IGNORECASE,
) -> tuple[str, int]:
    count = 0
    for pattern, repl in pairs:
        new_text, n = re.subn(pattern, repl, text, flags=flags)
        if n:
            text = new_text
            count += n
    return text, count


def _apply_synonyms(text: str, strength: int, rng: random.Random) -> tuple[str, int]:
    """Swap some synonyms; higher strength = more swaps."""
    prob = {1: 0.25, 2: 0.45, 3: 0.7}.get(strength, 0.45)
    count = 0

    def make_replacer(options: list[str]) -> Callable[[re.Match], str]:
        def _repl(m: re.Match) -> str:
            nonlocal count
            if rng.random() > prob:
                return m.group(0)
            pick = rng.choice(options)
            # Preserve capitalization of first letter
            orig = m.group(0)
            if orig[0].isupper():
                pick = pick[0].upper() + pick[1:]
            count += 1
            return pick

        return _repl

    for pattern, options in SYNONYM_SWAPS:
        text = re.sub(pattern, make_replacer(options), text, flags=re.IGNORECASE)
    return text, count


def _split_sentences(text: str) -> list[str]:
    # Keep sentence-ending punctuation attached
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _word_count(s: str) -> int:
    return len(re.findall(r"\b\w+\b", s))


def _rhythm_pass(
    sentences: list[str],
    strength: int,
    profile: dict,
    rng: random.Random,
) -> tuple[list[str], list[str]]:
    """Vary sentence length / structure for burstiness."""
    notes: list[str] = []
    if not sentences:
        return sentences, notes

    out: list[str] = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        wc = _word_count(s)

        # Break long parallel "X, Y, and Z" list-y sentences at strength >= 2
        if strength >= 2 and wc > 28 and re.search(r",\s+[^,]+,\s+(?:and|or)\s+", s):
            # Try to split on semicolon or mid-list commas into shorter beats
            chunks = re.split(r";\s+", s)
            if len(chunks) > 1:
                out.extend(c if c.endswith((".", "!", "?")) else c + "." for c in chunks)
                notes.append("Broke long parallel clauses for rhythm")
                i += 1
                continue

        # Merge two very short consecutive sentences occasionally (strength 1 keeps more shorts)
        if (
            strength >= 2
            and wc <= 5
            and i + 1 < len(sentences)
            and _word_count(sentences[i + 1]) <= 8
            and rng.random() < 0.35
        ):
            a = s.rstrip(".!?")
            b = sentences[i + 1]
            merged = f"{a} — {b[0].lower()}{b[1:]}" if b else s
            out.append(merged)
            notes.append("Merged short beats for flow")
            i += 2
            continue

        # At high strength, occasionally turn a medium sentence into a short punch + remainder
        if strength >= 3 and 12 <= wc <= 22 and rng.random() < 0.3:
            words = s.split()
            cut = max(3, wc // 3)
            first = " ".join(words[:cut]).rstrip(",;")
            if not first.endswith((".", "!", "?")):
                first += "."
            rest = " ".join(words[cut:])
            if rest:
                rest = rest[0].upper() + rest[1:]
                if not rest.endswith((".", "!", "?")):
                    rest += "."
                out.append(first)
                out.append(rest)
                notes.append("Split for punchy rhythm")
                i += 1
                continue

        # Allow And/But starts (casual)
        if profile.get("start_and_but") and strength >= 2 and i > 0:
            if s.lower().startswith(("however ", "therefore ", "thus ")):
                s = re.sub(
                    r"^(however|therefore|thus)\b,?\s*",
                    rng.choice(["But ", "And ", "Still, "]),
                    s,
                    flags=re.IGNORECASE,
                    count=1,
                )
                notes.append("Swapped stiff transition for And/But")

        out.append(s)
        i += 1

    # Uneven paragraphing: group into paragraphs of mixed size
    return out, notes


def _voice_pass(text: str, profile: dict, strength: int) -> tuple[str, list[str]]:
    notes: list[str] = []
    if profile.get("contractions") and strength >= 1:
        text, n = _apply_replacements(text, CONTRACTIONS, flags=0)
        if n:
            notes.append("Added natural contractions")

    if profile.get("soften") and strength >= 2:
        text, n = _apply_replacements(text, ABSOLUTE_SOFTENERS, flags=re.IGNORECASE)
        if n:
            notes.append("Softened absolute claims")

    # Prefer concrete: "the implementation of X" → "implementing X" light touch
    text2, n = re.subn(
        r"\bthe (implementation|utilization|application|development|creation|use) of\b",
        lambda m: {
            "implementation": "implementing",
            "utilization": "using",
            "application": "applying",
            "development": "building",
            "creation": "making",
            "use": "using",
        }.get(m.group(1).lower(), m.group(0)),
        text,
        flags=re.IGNORECASE,
    )
    if n:
        text = text2
        notes.append("Swapped abstract nouns for verbs")

    return text, notes


def _cleanup(text: str) -> str:
    # Collapse whitespace, fix double spaces, fix " .", capitalize sentence starts
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +([,.!?;:])", r"\1", text)
    text = re.sub(r"([.!?])([A-Za-z])", r"\1 \2", text)
    # Fix empty leftovers from phrase deletion
    text = re.sub(r"^\s*,\s*", "", text)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r"  +", " ", text)

    # Capitalize after sentence boundaries
    def cap_sentences(s: str) -> str:
        parts = re.split(r"([.!?]\s+)", s)
        result = []
        for i, part in enumerate(parts):
            if i == 0 or (i > 0 and re.match(r"[.!?]\s+", parts[i - 1] if i else "")):
                if part and part[0].islower():
                    part = part[0].upper() + part[1:]
            result.append(part)
        return "".join(result)

    # Paragraph-aware
    paras = text.split("\n")
    paras = [cap_sentences(p.strip()) if p.strip() else p for p in paras]
    text = "\n".join(paras).strip()

    # Remove orphan commas at line start
    text = re.sub(r"(^|\n),\s*", r"\1", text)
    # Fix doubled articles / leftover "a a" / "the the"
    text = re.sub(r"\b(a|an|the)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    # a → an before vowel sounds (simple heuristic)
    text = re.sub(r"\ba ([aeiouAEIOU])", r"an \1", text)
    # Collapse leftover double spaces from empty replacements
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"\s+([,.])", r"\1", text)
    # "will Verb" where Verb is bare infinitive already ok; fix "will helping" style if any
    text = re.sub(r"\bwill (looking|using|helping|building|showing|improving|starting)\b",
                  lambda m: "will " + {
                      "looking": "look", "using": "use", "helping": "help",
                      "building": "build", "showing": "show", "improving": "improve",
                      "starting": "start",
                  }[m.group(1)], text, flags=re.IGNORECASE)
    # Soften "with Verb-ing X" → keep; fix "with open up" leftovers
    text = re.sub(r"\b(?:with|for) (?:open up|tapping)(?: potential)?\b", "to unlock potential", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdeal with\s+world of\b", "deal with", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdeal with\s+area of\b", "deal with", text, flags=re.IGNORECASE)
    # Ensure sentences start capitalized after aggressive deletions
    def _cap_line(line: str) -> str:
        line = line.strip()
        if not line:
            return line
        return line[0].upper() + line[1:] if line[0].islower() else line
    text = "\n".join(_cap_line(L) if L.strip() else L for L in text.split("\n"))
    return text


def _reparagraph(sentences: list[str], strength: int, rng: random.Random) -> str:
    """Build paragraphs with uneven lengths."""
    if not sentences:
        return ""
    if strength == 1:
        # Keep closer to original flow — one block or light breaks
        return " ".join(sentences)

    paras: list[str] = []
    buf: list[str] = []
    target = rng.choice([1, 2, 2, 3, 3, 4])
    for s in sentences:
        buf.append(s)
        if len(buf) >= target:
            paras.append(" ".join(buf))
            buf = []
            target = rng.choice([1, 2, 2, 3, 1, 3, 4] if strength >= 3 else [2, 2, 3, 3, 4])
    if buf:
        paras.append(" ".join(buf))
    return "\n\n".join(paras)


def _unique_pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for pat, repl in pairs:
        if pat in seen:
            continue
        seen.add(pat)
        out.append((pat, repl))
    return out


_AI_PAIRS = _unique_pairs(AI_PHRASE_REPLACEMENTS)


def _demolish_aitells(text: str) -> tuple[str, int]:
    return _apply_replacements(text, _AI_PAIRS, flags=re.IGNORECASE)


def local_humanize(
    text: str,
    mode: str = "casual",
    strength: int = 2,
    seed: int | None = None,
) -> HumanizeResult:
    if not text or not text.strip():
        return HumanizeResult(output="", changes=["Empty input"])

    mode = mode if mode in MODE_PROFILES else "casual"
    strength = max(1, min(3, int(strength)))
    profile = MODE_PROFILES[mode]
    rng = random.Random(seed if seed is not None else hash(text) % (2**32))

    changes: list[str] = []
    working = text.strip()

    # Pass 1: AI-tell demolition (always; scale by strength)
    demolished, n_ai = _demolish_aitells(working)
    if strength == 1:
        # Light: only apply if many hits; still apply but note lightly
        working = demolished
    else:
        working = demolished
    if n_ai:
        changes.append(f"Cleared {n_ai} AI-pattern phrase(s)")

    # Pass 2: voice
    working, voice_notes = _voice_pass(working, profile, strength)
    changes.extend(voice_notes)

    # Pass 3: synonyms / paraphrase
    if strength >= 2 or (strength == 1 and n_ai < 3):
        working, n_syn = _apply_synonyms(working, strength, rng)
        if n_syn:
            changes.append(f"Paraphrased {n_syn} wording choice(s)")

    # Pass 4: rhythm
    sentences = _split_sentences(working)
    sentences, rhythm_notes = _rhythm_pass(sentences, strength, profile, rng)
    for note in rhythm_notes:
        if note not in changes:
            changes.append(note)

    # Occasional fragment for casual high strength
    if profile.get("fragments_ok") and strength >= 3 and sentences and rng.random() < 0.25:
        # Shorten last sentence into a fragment vibe if long enough
        last = sentences[-1]
        if _word_count(last) > 10 and last.endswith("."):
            # Pull a short trailing emphasis
            sentences.append("Simple as that.")
            changes.append("Added a natural fragment beat")

    working = _reparagraph(sentences, strength, rng)
    working = _cleanup(working)

    # Academic-light: expand a few contractions back if accidental
    if mode == "academic-light":
        back = [
            (r"\bit's\b", "it is"),
            (r"\bIt's\b", "It is"),
            (r"\bdon't\b", "do not"),
            (r"\bDon't\b", "Do not"),
            (r"\bcan't\b", "cannot"),
            (r"\bCan't\b", "Cannot"),
            (r"\bwon't\b", "will not"),
            (r"\bwe're\b", "we are"),
            (r"\bWe're\b", "We are"),
            (r"\bthey're\b", "they are"),
            (r"\blet's\b", "let us"),
        ]
        working, n = _apply_replacements(working, back, flags=0)
        if n:
            changes.append("Kept academic-light tone (fewer contractions)")

    if not changes:
        changes.append("Light polish — already fairly natural")

    # Deduplicate change notes while preserving order
    seen = set()
    uniq = []
    for c in changes:
        if c not in seen:
            seen.add(c)
            uniq.append(c)

    return HumanizeResult(output=working, changes=uniq)


def llm_humanize(
    text: str,
    mode: str = "casual",
    strength: int = 2,
) -> HumanizeResult | None:
    """Optional OpenAI-compatible rewrite if OPENAI_API_KEY is set."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    strength_label = {1: "light polish", 2: "moderate rewrite", 3: "aggressive rewrite"}.get(
        strength, "moderate rewrite"
    )
    mode_hint = {
        "casual": "conversational, contractions OK, natural and imperfect",
        "professional": "clear business prose, still human, light contractions OK",
        "academic-light": "clear scholarly tone without stuffiness; avoid slang",
    }.get(mode, "natural")

    system = (
        "You rewrite text so it sounds like a real person wrote it: natural rhythm, "
        "varied sentence length, fewer AI clichés. Keep the same meaning and facts — "
        "never invent details. Do not claim the result is undetectable. "
        "Return ONLY the rewritten text, no preamble."
    )
    user = (
        f"Mode: {mode} ({mode_hint}). Strength: {strength} ({strength_label}).\n\n"
        f"Text:\n{text}"
    )

    try:
        import json
        import urllib.request

        payload = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7 + 0.1 * strength,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        return HumanizeResult(
            output=content,
            changes=["LLM rewrite mode", f"Mode: {mode}", f"Strength: {strength}"],
        )
    except Exception as exc:  # noqa: BLE001 — fall back to local
        local = local_humanize(text, mode=mode, strength=strength)
        local.changes.insert(0, f"LLM unavailable ({type(exc).__name__}); used local engine")
        return local


def humanize(
    text: str,
    mode: str = "casual",
    strength: int = 2,
    prefer_llm: bool = True,
) -> HumanizeResult:
    if prefer_llm and os.environ.get("OPENAI_API_KEY", "").strip():
        result = llm_humanize(text, mode=mode, strength=strength)
        if result is not None:
            return result
    return local_humanize(text, mode=mode, strength=strength)
