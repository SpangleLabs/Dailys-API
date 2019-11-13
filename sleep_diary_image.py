from PIL import Image, ImageDraw

col_table_bg = (124, 124, 124)
col_border = (0, 0, 0)
col_text = (0, 0, 0)

HOURS = 24
pix_per_hour = 20
start_hour = 18
table_width = pix_per_hour * HOURS

im = Image.new("RGBA", (table_width, 100))

draw = ImageDraw.Draw(im)
draw.rectangle([(0,30), (table_width, 70)], col_table_bg, col_border, 1)

am_width, _ = draw.textsize("am")
pm_width, _ = draw.textsize("pm")
midnight_width, _ = draw.textsize("midnight")
noon_width, _ = draw.textsize("noon")
if start_hour > 12:
    draw.text((0,0), "pm", col_text)
    midnight_x = ((24-start_hour)*pix_per_hour)-midnight_width//2
    draw.text((midnight_x, 0), "midnight", col_text)
    am_x = ((26-start_hour)*pix_per_hour)
    draw.text((am_x, 0), "am", col_text)
    noon_x = ((36-start_hour)*pix_per_hour)-noon_width//2
    draw.text((noon_x, 0), "noon", col_text)
    draw.text((table_width-pm_width, 0), "pm", col_text)
elif start_hour == 12:
    draw.text((0,0), "noon", col_text)
    pm_x = (2*pix_per_hour)
    draw.text((pm_x, 0), "pm", col_text)
    midnight_x = (12*pix_per_hour) - midnight_width//2
    draw.text((midnight_x, 0), "midnight", col_text)
    am_x = (14*pix_per_hour)
    draw.text((am_x, 0), "am", col_text)
    draw.text((table_width-noon_width, 0), "noon", col_text)
elif start_hour == 0:
    draw.text((0,0), "midnight", col_text)
    am_x = midnight_width + pix_per_hour
    draw.text((am_x, 0), "am", col_text)
    noon_x = (12*pix_per_hour) - noon_width//2
    draw.text((noon_x, 0), "noon", col_text)
    pm_x = (14*pix_per_hour)
    draw.text((pm_x, 0), "pm", col_text)
    draw.text((table_width-midnight_width, 0), "midnight", col_text)
else:
    draw.text((0,0), "am", col_text)
    noon_x = (12-start_hour) * pix_per_hour - noon_width//2
    draw.text((noon_x, 0), "noon", col_text)
    pm_x = (14-start_hour) * pix_per_hour
    draw.text((pm_x, 0), "pm", col_text)
    midnight_x = (24-start_hour) * pix_per_hour - midnight_width//2
    draw.text((midnight_x, 0), "midnight", col_text)
    draw.text((table_width-am_width, 0), "am", col_text)


for hour in range(HOURS + 1):
    line_x = hour*pix_per_hour
    if hour % 2 == 0:
        text = str(((hour+start_hour-1)%12)+1)
        text_width, _ = draw.textsize(text)
        if hour == 0:
            text_x = line_x
        elif hour == HOURS:
            text_x = line_x - text_width
        else:
            text_x = line_x - text_width//2
        draw.text((text_x, 15), text, col_text)
    draw.line([(line_x, 30), (line_x, 70)], col_border)

# write to stdout
im.save("./image-test.png", "PNG")
