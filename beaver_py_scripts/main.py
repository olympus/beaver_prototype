import lvgl as lv
import epd_hal

g_epd = epd_hal.EPD_2in66()

class Color:
    NONE = 0
    WHITE = 1
    RED = 2
    BLACK = 3

def rgb565_to_eink(low_byte, high_byte) -> int:
    # Extract RGB components from RGB565
    red   = (high_byte & 0xF8)  # 5 bits of red (0-248 in steps of 8)
    green = ((high_byte & 0x07) << 3) | ((low_byte & 0xE0) >> 5)  # 6 bits of green (0-252 in steps of 4)
    blue  = (low_byte & 0x1F)   # 5 bits of blue (0-248 in steps of 8)

    # Map colorshades back to completely red, black or white
    if red >= 160 and green < 40 and blue < 40:  
        return Color.RED 
    elif red < 100 and green < 100 and blue < 100:
        return Color.BLACK
    else:
        return Color.WHITE



def flush_cb(lv_display, area, lv_px_map):
    print("Flushing...")
    print("Area: x1={}, y1={}, x2={}, y2={}".format(
        area.x1, area.y1, area.x2, area.y2
    ))

    width, height = g_epd.GetDimensions()
   
    # Where does the area being flushed start and how big is it?
    x_start = area.x1
    x_delta = area.x2 - area.x1 + 1

    y_start = area.y1
    y_delta = area.y2 - area.y1 + 1

    # 2 byte i.e. 16bit per pixel as per rgb565
    buffer_size = int(x_delta * y_delta * 2)
    
    # extracting data from c-style array into python bytearray 
    buf = bytearray(lv_px_map.__dereference__(buffer_size))

    for y_rel in range(y_delta):
        y_abs = y_rel + y_start
        for x_rel in range(x_delta):
            x_abs = width - (x_rel + x_start)

            buf_index = int (x_rel + y_rel * width) #why not y_delta?
            if(buf_index >= len(buf)):
                print(f"out of range with coord x:{x_rel}, y:{y_rel}, index:{buf_index}")
                continue

            # Unpacking of pixelinformation
            low_byte = buf[ buf_index * 2 ]
            high_byte = buf [buf_index * 2 + 1]

            # Mapping of 16bit RGB565 Colorspace into eInk Colorspace

            # This is probably not optimal as the entire image_landscape buffer exists in memory on the mcu
            # epd also stores another separate image_portrait buffer with the same size, that isn't being used
            # as LVGL supports partial screen updates, it would be better to stream lv_px_map to the eInk display directly and
            # only on the last call to flush_cb to make the eInk present the internal buffer. This however wouold require a partial rewrite
            # of the eInk driver (making use of the Set RAM X-/Y-Address Start End position functionality in order to allow for writing into
            # arbitrary locations on the eInk. This is specified on Page 22 in the eInk specification)

            color = rgb565_to_eink(low_byte, high_byte)

            if(color == Color.WHITE):
                g_epd.image_landscape_black.pixel(y_abs, x_abs, 1)
                g_epd.image_landscape_red.pixel(y_abs, x_abs, 0)
            elif(color == Color.BLACK):
                g_epd.image_landscape_black.pixel(y_abs, x_abs, 0)
                g_epd.image_landscape_red.pixel(y_abs, x_abs, 0)
            elif(color == Color.RED):
                g_epd.image_landscape_black.pixel(y_abs, x_abs, 1)
                g_epd.image_landscape_red.pixel(y_abs, x_abs, 1)
            else:
                print(f"(This ain't no color, bruh) Tried writing {low_byte};{high_byte} to coord x:{x_rel}, y:{y_rel}, index:{buf_index}")

    # Notify LVGL that flushing is done
    lv_display.flush_ready()

def draw_label():
    scr = lv.obj()

    label = lv.label(scr)
    label.set_text("Hallo Welt")
    label.set_style_text_color(lv.color_black(), lv.PART.MAIN)
    label.center()

    lv.screen_load(scr)

def draw_line(points, color):
    line_style = lv.style_t()
    line_style.set_line_width(2)
    line_style.set_line_color(color)
    line_style.set_line_rounded(True)

    line1 = lv.line(lv.screen_active())
    line1.set_points(points, len(points))
    line1.add_style(line_style, lv.PART.MAIN)


def example(epd):
    print("Running example")
    width, height = epd.GetDimensions()

    # 2byte per pixel. LVGL allows for working with buf
    # n of the size needed for the entire display, thus / 10
    bufsize = int(width * height * 2 / 10) 
    buf1 =  bytearray(bufsize * [0x00]) 

    # Minimal setup for drawing stuff
    lv.init()
    
    display = lv.display_create(width, height)
    display.set_color_format(lv.COLOR_FORMAT.RGB565) #L8 not supported yet? 

    rendermode = lv.DISPLAY_RENDER_MODE.PARTIAL #DIRECT/FULL needs bigger buffers, as specified in docs
    display.set_buffers(buf1, None, bufsize, rendermode)
    display.set_flush_cb(flush_cb)

    screen = lv.screen_active()
    screen.set_style_bg_color(lv.color_white(),  lv.PART.MAIN)

    label = lv.label(lv.screen_active())
    label.set_text("Hallo Welt")
    #label.set_style_text_font(lv.font_montserrat_14)
    #label.set_style_text_color(lv.color_hex(0xff0000), lv.PART.MAIN)
    label.set_style_text_color(lv.color_black(), lv.PART.MAIN)
    label.center()


    line_points1 = [
        lv.point_precise_t({'x': 5, 'y': 5}),
        lv.point_precise_t({'x': width - 5, 'y': 5}),
        lv.point_precise_t({'x': width - 5, 'y': height - 5}),
        lv.point_precise_t({'x': 5, 'y': height - 5}),
        lv.point_precise_t({'x': 5, 'y': 5}),
    ]

    line_points2 = [
        lv.point_precise_t({'x': 10, 'y': 10}),
        lv.point_precise_t({'x': width - 10, 'y': 10}),
        lv.point_precise_t({'x': width - 10, 'y': height - 10}),
        lv.point_precise_t({'x': 10, 'y': height - 10}),
        lv.point_precise_t({'x': 10, 'y': 10}),
    ]


    draw_line(line_points1, lv.color_black())
    draw_line(line_points2, lv.color_hex(0xff0000)) #red line (red is choosen automagically as sopon as it isn't black / white)


    epd.Clear(0xff)
    # image landscape is for black
    # image portrait is for red
    epd.image_landscape_black.fill(0xff)
    epd.image_landscape_red.fill(0x00) # clear color is different to black 
    
    lv.refr_now(display)

    print("Uploading buffers to eInk")
    epd.display_Landscape(epd.buffer_landscape_black, 0x24)
    epd.display_Landscape(epd.buffer_landscape_red, 0x26)
    print("Updating display")
    epd.TurnOnDisplay()


if __name__=='__main__':
    print("Main ==>")
    print(dir(lv.FONT_SUBPX))
    
    example(g_epd)
    print("Main <==")