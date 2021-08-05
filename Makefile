TARGET = autograder.zip

ZIP = zip

# Directories whose .py files will be placed in the output.
SRC_DIRS = engine

# Directories whose entire contents will be placed in the output.
AUX_DIRS = keys

GLOBS = * */* */*/* */*/*/* */*/*/*/* */*/*/*/*/* */*/*/*/*/*/* */*/*/*/*/*/*/*

SRCS = setup.sh \
	   run_autograder \
	   requirements.txt \
	   generate.py \
	   $(foreach DIR,$(SRC_DIRS),$(wildcard $(patsubst %,$(DIR)/%.py,$(GLOBS)))) \
	   $(foreach DIR,$(AUX_DIRS),$(wildcard $(patsubst %,$(DIR)/%,$(GLOBS))))

.PHONY: all
all: $(TARGET)

$(TARGET): $(SRCS)
	$(ZIP) $@ $^

.PHONY: clean
clean:
	rm -rf $(TARGET)
