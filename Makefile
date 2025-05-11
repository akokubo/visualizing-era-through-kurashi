epub/時代のイメージをとらえるための授業分析.epub: README.md cover.jpg Makefile styles.css metadata.yml
	pandoc -o epub/時代のイメージをとらえるための授業分析.epub -t epub3 --epub-cover-image=cover.jpg --css=styles.css --toc metadata.yml README.md
