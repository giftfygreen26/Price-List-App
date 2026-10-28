/* ============================================================================
   Cloud sync configuration — Google Sheets + Apps Script backend.
   The app reads live product/price data from this endpoint on load, and
   pushes admin edits back to it so changes are shared across every device
   instead of being trapped in one browser's localStorage.
   ============================================================================ */
const API_URL = "https://script.google.com/macros/s/AKfycbxer7KkSYQENMEP0PomkUPxsuRg3fOA6IP9ubdxzrfnuaWTJe_LX_zv9lCn-J8lvdIQBg/exec";
const API_KEY = "UUtFRGitp_z2MRd-nSJecn0KR8NRHCrV";
