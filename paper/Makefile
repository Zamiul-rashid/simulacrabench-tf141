main.pdf: main.tex refs.bib neurips_2026.sty
	@if command -v tectonic >/dev/null; then tectonic -X compile main.tex; else latexmk -pdf main.tex; fi
