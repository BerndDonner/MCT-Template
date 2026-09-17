# ------------------------------------------------------------
# 🧩 Simple AVR Makefile (compatible with Arduino core)
# ------------------------------------------------------------

# 🔧 MCU and clock
MCU       = atmega328p
F_CPU     = 16000000UL
PORT      = /dev/ttyACM0
BAUD      = 115200

# 🔧 Paths to Arduino core
ARDUINO_BASE = $(HOME)/.arduino15/packages/arduino/hardware/avr/1.8.6
CORE     = $(ARDUINO_BASE)/cores/arduino
VARIANT  = $(ARDUINO_BASE)/variants/standard

# 🔧 Toolchain
CC       = avr-gcc
CXX      = avr-g++
OBJCOPY  = avr-objcopy
AR       = avr-ar
DUDE     = avrdude

# 🔧 Compiler flags
CFLAGS   = -Os -DF_CPU=$(F_CPU) -mmcu=$(MCU) -I$(CORE) -I$(VARIANT)
CXXFLAGS = $(CFLAGS) -std=gnu++17
LDFLAGS  = -mmcu=$(MCU)

# 🔧 Files
TARGET   = blink
SRC      = $(TARGET).cpp
BUILD    = build

CORE_OBJS = $(patsubst $(CORE)/%.c,$(BUILD)/core/%.o,$(wildcard $(CORE)/*.c)) \
            $(patsubst $(CORE)/%.cpp,$(BUILD)/core/%.o,$(wildcard $(CORE)/*.cpp))

# ------------------------------------------------------------
# 🧱 Rules
# ------------------------------------------------------------

all: $(BUILD)/$(TARGET).hex

# Compile Arduino core
$(BUILD)/core/%.o: $(CORE)/%.c | $(BUILD)/core
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/core/%.o: $(CORE)/%.cpp | $(BUILD)/core
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Create library
$(BUILD)/libarduino.a: $(CORE_OBJS)
	$(AR) rcs $@ $^

# Compile your sketch
$(BUILD)/$(TARGET).o: $(SRC) | $(BUILD)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Link everything
$(BUILD)/$(TARGET).elf: $(BUILD)/$(TARGET).o $(BUILD)/libarduino.a
	$(CXX) $(LDFLAGS) $^ -o $@

# Create HEX for upload
$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@

# Upload
upload: $(BUILD)/$(TARGET).hex
	$(DUDE) -v -p$(MCU) -carduino -P$(PORT) -b$(BAUD) -D -Uflash:w:$<:i

# Create build dirs
$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/core:
	mkdir -p $(BUILD)/core

# Clean
clean:
	rm -rf $(BUILD)

.PHONY: all upload clean

