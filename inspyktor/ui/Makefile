PYFILES = $(patsubst %.ui,%.py,$(wildcard *.ui))

all: $(PYFILES)

clean:
	rm -f *.pyc
	rm -f $(PYFILES) $(patsubst %.py,%.pyc,$(PYFILES))

%.py: %.ui
	pykdeuic4 -o $@ $^
