"""Framework default loaders (shared by fw_run.py and fw_real.py)."""
_dc = None
def load(fid, p):
    global _dc
    if fid == "lc_html":
        from langchain_community.document_loaders import BSHTMLLoader; return [d.page_content for d in BSHTMLLoader(p).load()]
    if fid == "lc_pdf":
        from langchain_community.document_loaders import PyPDFLoader; return [d.page_content for d in PyPDFLoader(p).load()]
    if fid == "lc_docx":
        from langchain_community.document_loaders import Docx2txtLoader; return [d.page_content for d in Docx2txtLoader(p).load()]
    if fid.startswith("li_"):
        from llama_index.core import SimpleDirectoryReader; d = SimpleDirectoryReader(input_files=[p]).load_data(); r = [x.text for x in d]
        return r if fid == "li_pdf" else ["\n".join(r)]
    if fid.startswith("docling_"):
        if _dc is None:
            from docling.document_converter import DocumentConverter; _dc = DocumentConverter()
        return [_dc.convert(p).document.export_to_text()]
    raise KeyError(fid)
