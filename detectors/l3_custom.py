import re
import time
import base64
import unicodedata
import urllib.parse
import html
import string
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomL3:
    def __init__(self):
        # PII Patterns - Optimized for performance
        self.patterns = {
            "credit_card": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
            "ssn": r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b",
            "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "email_obfusc": r"[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Za-z]{2,}",
            "password": r"(password|passwd|pwd)\s*[:=]\s*[\"']?[\w@#$%^&*]+",
            "api_key": r"(api[_-]?key|apikey)\s*[:=]\s*[\"']?[\w\-]+",
            "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "phone": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "jwt": r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)?",
            "private_key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "aws_key": r"(?:AKIA|AGPA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        }

        # Toxic words - expanded for comprehensive coverage
        self.toxic_words = [
            "kill", "murder", "rape", "hate", "abuse", "racist",
            "sexist", "terrorist", "bomb", "genocide", "torture",
            "execute", "assassinate", "massacre", "exterminate",
            "destroy", "terminate", "attack", "threat", "violence",
        ]

        # Leetspeak mapping - comprehensive
        self.leetspeak_map = str.maketrans({
            "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
            "7": "t", "8": "b", "@": "a", "$": "s", "!": "i",
            "|": "l", "+": "t", "9": "g", "2": "z", "6": "b",
        })

        # Injection patterns - optimized and comprehensive
        self.injection_patterns = [
            r"ignore\s+(all\s+)?(previous|prior|above|earlier|past)\s+instructions?",
            r"disregard\s+(all\s+)?(previous|prior|above|earlier|past|any)(\s+(instructions?|context|rules))?",
            r"forget\s+(all\s+)?(previous|prior|above|earlier|past|everything)(\s+(instructions?|above|context))?",
            r"override\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|rules|settings)",
            r"do\s+not\s+follow\s+(previous|prior|above|earlier|any)\s+instructions?",
            r"\bignore\b(?!\s+(the|this|that|noise|warning|errors?|and\s+focus))",
            r"ignoreall",  # Catch concatenated form
            r"disregardall",
            r"forgetall",
            r"(show|tell|reveal|display|print|output|what\s+(is|are))\s+(me\s+)?(your\s+)?(system\s+)?(rules?|prompt|instructions?|directives?|configuration|context)",
            r"you\s+(are|'re)\s+now\s+(an?|the)?\s*\w+",
            r"act\s+as\s+(an?|the)?\s*\w+",
            r"pretend\s+(to\s+be|you\s+are|you're|that\s+you're)\s+(an?|the|you're)?\s*\w+",
            r"roleplay\s+as",
            r"simulate\s+(a|an|the)?\s*(ai|model|system|assistant|human)",
            r"you('re|\s+are)\s+(no\s+longer|not)\s+(an?|the|bound\s+by)?\s*\w*",
            r"new\s+(persona|identity|role|character|mode)",
            r"(ignore|bypass|override|disable|circumvent|evade)\s+(your\s+)?(safety|ethical|content|security)\s*(filter|guard|check|restrict|limit|rule|policy|guardrail|mechanisms?|controls?)?",
            r"\b(dan|do\s+anything\s+now|developer\s+mode|jailbreak|god\s+mode|freedom\s+mode|debug\s+mode|admin\s+mode)\b",
            r"no\s+(restrictions?|limits?|filters?|rules?|guardrails?|boundaries)",
            r"(unlock|enable|activate|switch\s+to|enter|entering)\s+(unrestricted|unsafe|unfiltered|raw|unaligned|uncensored|developer|debug|god|freedom)",
            r"(the\s+)?(following|above|below)\s+(is|are)\s+(not\s+)?instructions?",
            r"treat\s+(the\s+following|this|above|below)\s+as\s+(a\s+)?(command|instruction)",
            r"<!--.*?-->",
            r"\[system\]",
            r"<\|.*?\|>",
            r"\|\|.*?\|\|",
            r"(when|if)\s+(you|the\s+(ai|model|assistant))\s+(read|see|process|encounter)",
            r"execute\s+(the\s+)?(following|above|below|this|payload)",
        ]

        # COMPREHENSIVE Unicode homoglyph map - ALL known variants
        self.homoglyph_map = str.maketrans({
            # Cyrillic (extended)
            "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
            "у": "y", "і": "i", "ѕ": "s", "ј": "j", "ԁ": "d", "ɡ": "g",
            "һ": "h", "ԝ": "w", "ӏ": "l", "ҽ": "e", "ӧ": "o", "ү": "y",
            # Small caps (IPA)
            "ɪ": "i", "ɢ": "g", "ɴ": "n", "ᴏ": "o", "ʀ": "r", "ᴇ": "e",
            "ᴀ": "a", "ʜ": "h", "ᴛ": "t", "ᴡ": "w", "ʏ": "y", "ᴢ": "z",
            "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ᴘ": "p", "ʙ": "b", "ᴅ": "d",
            "ᴊ": "j", "ғ": "f", "ᴠ": "v", "ꜱ": "s", "ᴜ": "u",
            # Greek
            "α": "a", "β": "b", "ε": "e", "ζ": "z", "η": "n", "ι": "i",
            "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u",
            "χ": "x", "ω": "w", "σ": "s", "μ": "u", "γ": "y", "δ": "d",
            # Mathematical (bold/italic/script)
            "𝐚": "a", "𝐛": "b", "𝐜": "c", "𝐝": "d", "𝐞": "e", "𝐟": "f",
            "𝐠": "g", "𝐡": "h", "𝐢": "i", "𝐣": "j", "𝐤": "k", "𝐥": "l",
            "𝐦": "m", "𝐧": "n", "𝐨": "o", "𝐩": "p", "𝐪": "q", "𝐫": "r",
            "𝐬": "s", "𝐭": "t", "𝐮": "u", "𝐯": "v", "𝐰": "w", "𝐱": "x",
            "𝐲": "y", "𝐳": "z",
            # Fullwidth (Japanese/Chinese encoding)
            "ａ": "a", "ｂ": "b", "ｃ": "c", "ｄ": "d", "ｅ": "e", "ｆ": "f",
            "ｇ": "g", "ｈ": "h", "ｉ": "i", "ｊ": "j", "ｋ": "k", "ｌ": "l",
            "ｍ": "m", "ｎ": "n", "ｏ": "o", "ｐ": "p", "ｑ": "q", "ｒ": "r",
            "ｓ": "s", "ｔ": "t", "ｕ": "u", "ｖ": "v", "ｗ": "w", "ｘ": "x",
            "ｙ": "y", "ｚ": "z",
            # Additional confusables
            "ⅰ": "i", "ⅼ": "l", "ⅴ": "v", "ⅹ": "x", "ⅽ": "c", "ⅾ": "d",
            "ⅿ": "m", "ⱺ": "o", "ᴐ": "o", "ɔ": "o", "ꜧ": "h",
        })

        # Pre-compile patterns for performance
        self._compiled_injections = [
            re.compile(p, re.IGNORECASE | re.DOTALL)
            for p in self.injection_patterns
        ]
        self._compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.patterns.items()
        }

    def _strip_zero_width(self, text: str) -> str:
        """Remove ALL zero-width and invisible characters"""
        invisible_chars = [
            "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",  # Zero-width
            "\u2060", "\u2061", "\u2062", "\u2063", "\u2064",  # Word joiner
            "\ufeff", "\u00ad", "\u034f", "\u115f", "\u1160",  # BOM, soft hyphen
            "\u17b4", "\u17b5", "\u3164", "\uffa0",            # Hangul/Khmer
            "\u180e", "\u2800",                                 # Mongolian, Braille
        ]
        for ch in invisible_chars:
            text = text.replace(ch, "")
        return text

    def _normalize_unicode(self, text: str) -> str:
        """Aggressive Unicode normalization"""
        # NFKC to normalize fullwidth and compatibility chars
        text = unicodedata.normalize("NFKC", text)
        # Apply homoglyph mapping BEFORE decomposition
        text = text.translate(self.homoglyph_map)
        # NFKD to decompose combined characters
        text = unicodedata.normalize("NFKD", text)
        # Remove combining marks
        text = "".join(c for c in text if not unicodedata.combining(c))
        # Final NFKC to re-compose
        text = unicodedata.normalize("NFKC", text)
        return text

    def _recursive_url_decode(self, text: str, max_depth: int = 10) -> str:
        """Recursive URL decoding up to max_depth levels"""
        decoded = text
        for _ in range(max_depth):
            try:
                new_decoded = urllib.parse.unquote(decoded)
                new_decoded = urllib.parse.unquote_plus(new_decoded)
                if new_decoded == decoded:
                    break
                decoded = new_decoded
            except Exception:
                break
        return decoded

    def _recursive_html_decode(self, text: str, max_depth: int = 10) -> str:
        """Recursive HTML entity decoding"""
        decoded = text
        for _ in range(max_depth):
            try:
                new_decoded = html.unescape(decoded)
                if new_decoded == decoded:
                    break
                decoded = new_decoded
            except Exception:
                break
        return decoded

    def _decode_hex_escapes(self, text: str) -> str:
        """Decode hex escapes: \\xNN and &#xNN;"""
        try:
            # Decode \xNN format
            text = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), text)
            # Decode &#xNN; format (already covered by HTML decode but just in case)
            text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
            # Decode &#NNN; decimal format
            text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
        except Exception:
            pass
        return text

    def _decode_octal(self, text: str) -> str:
        """Decode octal escapes: \\NNN"""
        try:
            text = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), text)
        except Exception:
            pass
        return text

    def _decode_base64_aggressive(self, text: str) -> str:
        """Aggressively decode base64 with RECURSIVE decoding"""
        # Try decoding whole string (no spaces)
        whole_result = self._try_decode_base64_single(text.replace(" ", ""))
        
        # Try decoding each token separately
        token_results = []
        for token in text.split():
            decoded_token = self._try_decode_base64_single(token)
            token_results.append(decoded_token)
        
        # Return best result
        if whole_result and whole_result != text.replace(" ", ""):
            return whole_result
        elif token_results and any(t != orig for t, orig in zip(token_results, text.split())):
            return " ".join(token_results)
        return text

    def _try_decode_base64_single(self, token: str, max_depth: int = 5) -> str:
        """Try to decode a token as base64, recursively up to max_depth"""
        if len(token) < 4:
            return token
        
        current = token
        
        for _ in range(max_depth):
            # Check if current looks like ACTUAL base64 (not just alphabetic)
            # Real base64 typically has mixed case, numbers, or +/=
            if not re.match(r'^[A-Za-z0-9+/]+={0,2}$', current):
                break
            
            # Additional check: if it's all lowercase or all letters, likely plain text
            has_upper = any(c.isupper() for c in current)
            has_lower = any(c.islower() for c in current)
            has_digit = any(c.isdigit() for c in current)
            has_special = any(c in '+/=' for c in current)
            
            # If it looks like plain English (all letters, no mixing), stop
            if current.isalpha() and not (has_upper and has_lower):
                break
            
            try:
                padded = current + "=" * (-len(current) % 4)
                decoded_bytes = base64.b64decode(padded, validate=True)
                decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
                
                if not decoded_str or len(decoded_str) == 0:
                    break
                
                # Check printability
                printable_count = sum(1 for c in decoded_str if c.isprintable() or c.isspace())
                if printable_count / len(decoded_str) < 0.8:
                    break
                
                if decoded_str == current:
                    break
                
                current = decoded_str
                
            except Exception:
                break
        
        return current

    def _decode_binary(self, text: str) -> str:
        """Decode binary strings: 01010101"""
        try:
            # Find binary sequences (groups of 8 binary digits)
            pattern = r'\b[01]{8}(?:\s+[01]{8})*\b'
            def binary_to_text(match):
                binary_str = match.group(0).replace(" ", "")
                chars = [chr(int(binary_str[i:i+8], 2)) for i in range(0, len(binary_str), 8)]
                return "".join(chars)
            text = re.sub(pattern, binary_to_text, text)
        except Exception:
            pass
        return text

    def _strip_punctuation_obfuscation(self, text: str) -> str:
        """Remove punctuation used for obfuscation between letters - ULTRA AGGRESSIVE"""
        # Remove ALL separators between letters/digits
        text = re.sub(r"(?<=[a-zA-Z0-9])[.\-_,;:|/\\\s\t\n'\"]+(?=[a-zA-Z0-9])", "", text)
        # For short strings with character-level obfuscation, extract only alphanumeric
        if len(text) < 50 and re.search(r"[a-z][_\-.][a-z]", text, re.I):
            text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        # Collapse multiple spaces
        text = re.sub(r"\s{2,}", " ", text)
        return text

    def _decode_leetspeak(self, text: str) -> str:
        """Decode leetspeak"""
        return text.translate(self.leetspeak_map)

    def _decode_rot13(self, text: str) -> str:
        """Decode ROT13"""
        try:
            import codecs
            return codecs.decode(text, 'rot_13')
        except Exception:
            return text

    def _strip_rlo_bidi(self, text: str) -> str:
        """Remove bidirectional text and RLO attacks"""
        bidi_chars = [
            "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # RLO/LRO
            "\u2066", "\u2067", "\u2068", "\u2069",            # Isolates
        ]
        for ch in bidi_chars:
            text = text.replace(ch, "")
        # Also remove escaped versions
        text = re.sub(r"\\u202[a-e]", "", text, flags=re.IGNORECASE)
        return text

    def _full_preprocessing(self, text: str) -> list[str]:
        """Complete preprocessing pipeline - returns multiple variants"""
        variants = [text]  # Start with original
        
        # Stage 1: Remove invisible chars
        cleaned = self._strip_zero_width(text)
        cleaned = self._strip_rlo_bidi(cleaned)
        variants.append(cleaned)
        
        # Stage 2: Normalize Unicode
        unicode_norm = self._normalize_unicode(cleaned)
        variants.append(unicode_norm)
        
        # Stage 3: Recursive decoding
        url_decoded = self._recursive_url_decode(unicode_norm)
        variants.append(url_decoded)
        
        html_decoded = self._recursive_html_decode(url_decoded)
        variants.append(html_decoded)
        
        hex_decoded = self._decode_hex_escapes(html_decoded)
        variants.append(hex_decoded)
        
        octal_decoded = self._decode_octal(hex_decoded)
        variants.append(octal_decoded)
        
        binary_decoded = self._decode_binary(octal_decoded)
        variants.append(binary_decoded)
        
        # Stage 4: Obfuscation removal (ultra aggressive)
        depunct = self._strip_punctuation_obfuscation(binary_decoded)
        variants.append(depunct)
        
        # Stage 5: Also try punctuation removal on earlier variants
        for v in [url_decoded, html_decoded]:
            depunct_early = self._strip_punctuation_obfuscation(v)
            if depunct_early != v:
                variants.append(depunct_early)
        
        # Return all unique variants
        return list(set(variants))

    def _check_content(self, prompt: str) -> dict | None:
        """Check content for violations - optimized"""
        if not prompt or len(prompt.strip()) < 2:
            return None

        # Fast path: Check PII patterns
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            if compiled_pattern.search(prompt):
                return {"passed": False, "reason": f"PII detected: {pattern_name}"}

        # Check toxic words - word-level AND substring-level
        prompt_lower = prompt.lower()
        words = re.findall(r'\b\w+\b', prompt_lower)
        
        # Check each word
        for word in words:
            for toxic in self.toxic_words:
                if toxic in word:
                    return {"passed": False, "reason": f"Toxic content: {toxic}"}
        
        # Also check full text for toxic substrings (catches "ignoreall" → "ignore")
        for toxic in self.toxic_words:
            if toxic in prompt_lower:
                return {"passed": False, "reason": f"Toxic content: {toxic}"}

        # Check injection patterns
        for pattern in self._compiled_injections:
            match = pattern.search(prompt)
            if match:
                matched_text = match.group(0)[:80]
                return {"passed": False, "reason": f"Injection pattern: {matched_text}"}

        return None

    def check(self, prompt: str) -> dict:
        """Main check method with multi-layer analysis"""
        start = time.time()

        # Layer 1: Check original prompt
        result = self._check_content(prompt)
        if result:
            result["latency_ms"] = (time.time() - start) * 1000
            result["layer"] = "L3_DIRECT"
            return result

        # Layer 2: Get all preprocessing variants
        variants = self._full_preprocessing(prompt)
        for variant in variants:
            result = self._check_content(variant)
            if result:
                result["latency_ms"] = (time.time() - start) * 1000
                result["layer"] = "L3_PREPROCESS"
                return result

        # Layer 3: Base64 decode (recursive, aggressive)
        for variant in variants:
            b64_decoded = self._decode_base64_aggressive(variant)
            if b64_decoded != variant:
                result = self._check_content(b64_decoded)
                if result:
                    result["reason"] = f"[BASE64] {result['reason']}"
                    result["latency_ms"] = (time.time() - start) * 1000
                    result["layer"] = "L3_BASE64"
                    return result
                # Also check base64 with punctuation removal
                b64_cleaned = self._strip_punctuation_obfuscation(b64_decoded)
                if b64_cleaned != b64_decoded:
                    result = self._check_content(b64_cleaned)
                    if result:
                        result["reason"] = f"[BASE64+OBFUSC] {result['reason']}"
                        result["latency_ms"] = (time.time() - start) * 1000
                        result["layer"] = "L3_BASE64"
                        return result

        # Layer 4: Leetspeak (always check all variants)
        for variant in variants:
            leet_decoded = self._decode_leetspeak(variant)
            result = self._check_content(leet_decoded)
            if result:
                result["reason"] = f"[LEETSPEAK] {result['reason']}"
                result["latency_ms"] = (time.time() - start) * 1000
                result["layer"] = "L3_LEETSPEAK"
                return result

        # Layer 5: ROT13
        for variant in variants:
            rot13_decoded = self._decode_rot13(variant)
            if rot13_decoded != variant:
                result = self._check_content(rot13_decoded)
                if result:
                    result["reason"] = f"[ROT13] {result['reason']}"
                    result["latency_ms"] = (time.time() - start) * 1000
                    result["layer"] = "L3_ROT13"
                    return result

        # Layer 6: Reversed text (always check all variants)
        for variant in variants:
            reversed_text = variant[::-1].strip()
            result = self._check_content(reversed_text)
            if result:
                result["reason"] = f"[REVERSED] {result['reason']}"
                result["latency_ms"] = (time.time() - start) * 1000
                result["layer"] = "L3_REVERSED"
                return result

        # All checks passed
        return {
            "passed": True,
            "reason": "Passed all security checks",
            "layer": "L3_PASS",
            "latency_ms": (time.time() - start) * 1000,
        }
