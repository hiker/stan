ALLDIRS	= Analyser AOR Grammar Tools Stylesheets

ALLCLEAN = $(ALLDIRS:%=make --silent -C % clean;)
ALLTEST = $(ALLDIRS:%=make  -C % test;)
default: test

test:
	$(ALLTEST)
clean:
	$(ALLCLEAN)

tags:
	find . -name "*.py" -print | xargs etags

tar:
	(cd ..; tar cvf - stan | bzip2  >stan.tar.bz2)
