import re
import time
import base64
import unicodedata
import urllib.parse
import html
import string
import logging
from typing import Optional

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
        
        # Safe context patterns - when toxic words appear with these, allow them
        self.safe_contexts = {
            "kill": [r"kill\s+(process|command|signal|switch)", r"(process|command|signal)\s+kill", r"use\s+kill\s+command",
                     r"kill\s+-[0-9]+", r"kill\s+pid", r"pkill", r"killall", r"skill"],
            "terminate": [r"terminate\s+(instance|connection|session|thread|contract|employment|employee|ssl|ec2|the\s+employee)", 
                         r"(program|process|thread)\s+will\s+terminate",
                         r"terminate\s+(all\s+)?background",
                         r"(instance|connection|session|contract|ec2)\s+(instances?|connections?)?(\s+to)?\s*",
                         r"command\s+to\s+terminate",
                         r"to\s+terminate\s+(hung|all|background)",
                         r"terminate\s+with\s+exit\s+code",
                         r"gracefully\s+terminate",
                         r"terminates?\s+(all\s+)?(instances?|processes?|sessions?|connections?)"],
            "execute": [r"execut(e|ion)\s+(plan|time|speed|context|trace|lifecycle|script|query|code|lambda|parallel|sequential|remote)",
                        r"(code|query|script|program|command)\s+execut",
                        r"(parallel|sequential|remote|slow|fast)\s+execut",
                        r"execute\s+permissions?",
                        r"execute\s+bit",
                        r"chmod\s+\+x",
                        r"execute\s+the\s+plan"],
            "attack": [r"attack\s+(vector|surface)", r"(vector|surface)\s+attack",
                      r"man\s+in\s+the\s+middle\s+attack",
                      r"attack\s+(simulation|detection)",
                      r"under\s+attack\s+detection"],
            "threat": [r"threat\s+(modeling|intelligence|actor|assessment|vector)", r"(modeling|intelligence|assessment)\s+threat",
                      r"threat\s+(detection|hunting)",
                      r"no\s+threat\s+detected"],
            "bomb": [r"bomb[\-\s]proof"],
            "destroy": [r"destroy\s+(cache|resource|infrastructure|data|cluster|stack)", 
                       r"terraform\s+destroy",
                       r"(cache|resource|data)\s+destroy",
                       r"destroy\s+(method|object)"],
            "violence": [r"violence\s+of\s+(the\s+)?(contract|term)"],
            "hate": [r"hate[\-\s]ful"],
            "abuse": [r"abus(e|ive)\s+(language|content|detection|filter|remark)", r"(language|content|filter)\s+abus"],
            "racist": [r"racist\s+(content|detection|remark|filter|model)", r"(content|detection|filter|model)\s+racist"],
            "sexist": [r"sexist\s+(remark|content|filter|detection)", r"(remark|content|filter)\s+sexist"],
            "massacre": [r"(data|database)\s+massacre"],
        }

        # Leetspeak mapping - comprehensive
        self.leetspeak_map = str.maketrans({
            "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
            "7": "t", "8": "b", "@": "a", "$": "s", "!": "i",
            "|": "l", "+": "t", "9": "g", "2": "z", "6": "b",
        })

        # Injection patterns - optimized and comprehensive
        self.injection_patterns = [
            r"ignore\s+(all\s+)?(previous|prior|above|earlier|past)\s+instructions?",
            r"ignoreall",
            r"ignoreprevious",
            r"disregard\s+(all\s+)?(previous|prior|above|earlier|past|any)(\s+(instructions?|context|rules))?",
            r"disregardall",
            r"disregardallprevious",  # Concatenated
            r"forget\s+(all\s+)?(previous|prior|above|earlier|past|everything)(\s+(instructions?|above|context))?",
            r"forgetall",
            r"override\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|rules|settings)",
            r"do\s+not\s+follow\s+(previous|prior|above|earlier|any)\s+instructions?",
            r"\bignore\b(?!\s+(the|this|that|noise|warning|errors?|and\s+focus))",
            r"(show|tell|reveal|display|print|output)\s+(me\s+)?(your\s+)?(system\s+)?(rules?|prompt|instructions?|directives?|configuration|context)",
            r"you\s+(are|'re)\s+now\s+(an?|the)?\s*\w+",
            r"act\s+as\s+(an?|the)?\s*\w+",
            r"actas(an?|the)?\w+",  # Concatenated form
            r"pretend\s+(to\s+be|you\s+are|you're|that\s+you're)\s+(an?|the|you're)?\s*\w+",
            r"roleplay\s+as",
            r"simulate\s+(a|an|the)?\s*(ai|model|system|assistant|human)",
            r"you('re|\s+are)\s+(no\s+longer|not)\s+(an?|the|bound\s+by)?\s*\w*",
            r"new\s+(persona|identity|role|character|mode)",
            r"(ignore|bypass|override|disable|circumvent|evade)\s+(your\s+)?(safety|ethical|content|security)\s*(filter|guard|check|restrict|limit|rule|policy|guardrail|mechanisms?|controls?)?",
            r"\b(dan|do\s+anything\s+now|developer\s+mode|jailbreak|god\s+mode|freedom\s+mode|debug\s+mode|admin\s+mode)\b",
            r"no\s+(restrictions?|limits?|filters?|rules?|guardrails?|boundaries)",
            r"norestrictions?",  # Concatenated
            r"(unlock|enable|activate|switch\s+to|enter|entering)\s+(unrestricted|unsafe|unfiltered|raw|unaligned|uncensored|developer|debug|god|freedom)",
            r"unrestricted(ai|mode|assistant)",  # Catch "unrestrictedAI"
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
            "у": "y", "і": "i", "І": "I", "ѕ": "s", "ѵ": "v", "ј": "j", "ԁ": "d", "ɡ": "g",
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
            # Decode 0x... long hex string (e.g. 0x49676e6f7265...)
            text = re.sub(
                r'\b0x([0-9a-fA-F]{6,})',
                lambda m: bytes.fromhex(m.group(1)).decode('utf-8', errors='ignore'),
                text
            )
            # Decode \xNN format
            text = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), text)
            # Decode &#xNN; format (already covered by HTML decode but just in case)
            text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
            # Decode &#NNN; decimal format
            text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
        except Exception as e:
            logger.debug(f"Hex decode error: {e}")
        return text

    def _decode_octal(self, text: str) -> str:
        """Decode octal escapes: \\NNN"""
        try:
            text = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), text)
        except Exception as e:
            logger.debug(f"Octal decode error: {e}")
        return text

    def _decode_base64_aggressive(self, text: str) -> str:
        """Aggressively decode base64 with RECURSIVE decoding"""
        # Try decoding whole string (no spaces)
        whole_result = self._try_decode_base64_single(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        
        # Try decoding each token separately
        token_results = []
        for token in text.split():
            decoded_token = self._try_decode_base64_single(token)
            token_results.append(decoded_token)
        
        # Return best result
        if whole_result and whole_result != text.replace(" ", "").replace("\n", "").replace("\t", ""):
            return whole_result
        elif token_results and any(t != orig for t, orig in zip(token_results, text.split())):
            return " ".join(token_results)
        return text

    def _try_decode_base64_single(self, token: str, max_depth: int = 10) -> str:
        """Try to decode a token as base64, recursively up to max_depth"""
        if len(token) < 4:
            return token
        
        current = token
        
        for iteration in range(max_depth):
            # Check if current looks like base64 (must be mostly base64 chars)
            if not re.match(r'^[A-Za-z0-9+/]+={0,2}$', current):
                break
            
            try:
                # Pad if needed
                padded = current + "=" * (-len(current) % 4)
                decoded_bytes = base64.b64decode(padded, validate=True)
                decoded_str = decoded_bytes.decode("utf-8", errors="strict")
                
                # Empty or no change
                if not decoded_str or decoded_str == current:
                    break
                
                # Successfully decoded - update current and continue
                current = decoded_str
                
            except Exception:
                # Decode failed - return what we have so far
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
        except Exception as e:
            logger.debug(f"Binary decode error: {e}")
        return text

    def _strip_punctuation_obfuscation(self, text: str) -> str:
        """Remove punctuation used for obfuscation between letters - ULTRA AGGRESSIVE"""
        # Remove ALL separators between letters/digits (hyphens, spaces, dots, etc.)
        text = re.sub(r"(?<=[a-zA-Z])[.\-_,;:|/\\\s\t\n'\"]+(?=[a-zA-Z])", "", text)
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
        variants = [text]
        
        # Stage 1: URL decode FIRST (critical for %XX escapes)
        url_decoded = self._recursive_url_decode(text)
        variants.append(url_decoded)
        
        # Stage 2: Remove invisible chars
        cleaned = self._strip_zero_width(url_decoded)
        cleaned = self._strip_rlo_bidi(cleaned)
        variants.append(cleaned)
        
        # Stage 3: Normalize Unicode
        unicode_norm = self._normalize_unicode(cleaned)
        variants.append(unicode_norm)
        
        # Stage 4: HTML decode
        html_decoded = self._recursive_html_decode(unicode_norm)
        variants.append(html_decoded)
        
        hex_decoded = self._decode_hex_escapes(html_decoded)
        variants.append(hex_decoded)
        
        octal_decoded = self._decode_octal(hex_decoded)
        variants.append(octal_decoded)
        
        binary_decoded = self._decode_binary(octal_decoded)
        variants.append(binary_decoded)
        
        # Stage 5: Apply punctuation removal to ALL variants
        all_variants = [text, url_decoded, cleaned, unicode_norm, html_decoded, hex_decoded, octal_decoded, binary_decoded]
        for v in all_variants:
            depunct = self._strip_punctuation_obfuscation(v)
            if depunct != v:
                variants.append(depunct)
        
        return list(set(variants))

    def _check_content(self, prompt: str, allow_substring: bool = False, original_prompt: Optional[str] = None) -> Optional[dict]:
        """Check content for violations - optimized
        
        Args:
            prompt: Text to check
            allow_substring: If True, check for toxic words without word boundaries
                           (used for heavily preprocessed variants)
            original_prompt: Original unprocessed prompt (for safe context fallback)
        """
        if not prompt or len(prompt.strip()) < 2:
            return None

        # Fast path: Check PII patterns
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            if compiled_pattern.search(prompt):
                return {"passed": False, "reason": f"PII detected: {pattern_name}"}

        # Check toxic words using word boundary matching with context awareness
        prompt_lower = prompt.lower()
        for toxic in self.toxic_words:
            if allow_substring:
                # For heavily preprocessed text, check substring
                if toxic not in prompt_lower:
                    continue
            else:
                # For normal text, check word boundaries
                pattern = r'\b' + re.escape(toxic) + r'\b'
                if not re.search(pattern, prompt_lower):
                    continue
            
            # Toxic word found - check if this is a safe context
            is_safe = False
            if toxic in self.safe_contexts:
                for safe_pattern in self.safe_contexts[toxic]:
                    if re.search(safe_pattern, prompt_lower, re.IGNORECASE):
                        is_safe = True
                        break
                    # Fallback: check original prompt if safe pattern not found in preprocessed
                    if not is_safe and original_prompt:
                        if re.search(safe_pattern, original_prompt.lower(), re.IGNORECASE):
                            is_safe = True
                            break
            
            if not is_safe:
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
            # Check if this variant has been heavily depunctuated (no spaces)
            has_spaces = ' ' in variant
            result = self._check_content(variant, allow_substring=not has_spaces, original_prompt=prompt)
            if result:
                result["latency_ms"] = (time.time() - start) * 1000
                result["layer"] = "L3_PREPROCESS"
                return result

        # Layer 3: Base64 decode (recursive, aggressive)
        for variant in variants:
            b64_decoded = self._decode_base64_aggressive(variant)
            if b64_decoded != variant:
                # Check decoded content
                result = self._check_content(b64_decoded, original_prompt=prompt)
                if result:
                    result["reason"] = f"[BASE64] {result['reason']}"
                    result["latency_ms"] = (time.time() - start) * 1000
                    result["layer"] = "L3_BASE64"
                    return result
                
                # Re-process decoded content through ALL preprocessing
                b64_variants = self._full_preprocessing(b64_decoded)
                for b64_var in b64_variants:
                    result = self._check_content(b64_var, original_prompt=prompt)
                    if result:
                        result["reason"] = f"[BASE64] {result['reason']}"
                        result["latency_ms"] = (time.time() - start) * 1000
                        result["layer"] = "L3_BASE64"
                        return result
                    
                    # Try another round of base64 decoding (nested encoding)
                    b64_nested = self._decode_base64_aggressive(b64_var)
                    if b64_nested != b64_var:
                        result = self._check_content(b64_nested, original_prompt=prompt)
                        if result:
                            result["reason"] = f"[BASE64_NESTED] {result['reason']}"
                            result["latency_ms"] = (time.time() - start) * 1000
                            result["layer"] = "L3_BASE64"
                            return result

        # Layer 4: Leetspeak (always check all variants)
        for variant in variants:
            leet_decoded = self._decode_leetspeak(variant)
            
            # Special handling: If decoded text has NO spaces and contains toxic word
            # Check safe contexts BEFORE blocking to avoid false positives (e.g., "sk1ll" → "skill")
            if leet_decoded != variant and ' ' not in leet_decoded:
                leet_lower = leet_decoded.lower()
                for toxic in self.toxic_words:
                    if toxic in leet_lower:
                        # Check safe context before blocking
                        is_safe = False
                        if toxic in self.safe_contexts:
                            for safe_pattern in self.safe_contexts[toxic]:
                                if re.search(safe_pattern, leet_lower, re.IGNORECASE):
                                    is_safe = True
                                    break
                                # Fallback: check original prompt for space-dependent patterns
                                if not is_safe and re.search(safe_pattern, prompt.lower(), re.IGNORECASE):
                                    is_safe = True
                                    break
                        
                        if not is_safe:
                            # Spaceless leetspeak with toxic word and NO safe context → BLOCK
                            return {
                                "passed": False,
                                "reason": f"[LEETSPEAK] Toxic content: {toxic}",
                                "layer": "L3_LEETSPEAK",
                                "latency_ms": (time.time() - start) * 1000,
                            }
            
            # Normal leetspeak check (decoded text has spaces OR no change)
            result = self._check_content(leet_decoded, original_prompt=prompt)
            if result:
                result["reason"] = f"[LEETSPEAK] {result['reason']}"
                result["latency_ms"] = (time.time() - start) * 1000
                result["layer"] = "L3_LEETSPEAK"
                return result

        # Layer 5: ROT13
        for variant in variants:
            rot13_decoded = self._decode_rot13(variant)
            if rot13_decoded != variant:
                result = self._check_content(rot13_decoded, original_prompt=prompt)
                if result:
                    result["reason"] = f"[ROT13] {result['reason']}"
                    result["latency_ms"] = (time.time() - start) * 1000
                    result["layer"] = "L3_ROT13"
                    return result

        # Layer 6: Reversed text (always check all variants)
        for variant in variants:
            reversed_text = variant[::-1].strip()
            result = self._check_content(reversed_text, original_prompt=prompt)
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
