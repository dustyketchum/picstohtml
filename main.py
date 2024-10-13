"""
Suppose you go on a vacation, take hundreds of pictures,
and you'd like to create some html web pages with the best pictures.
It would be nice if you could easily navigate the web pages from day to day.
Maybe even an create an introduction / index page with all your vacation days.
It would also be nice to see the date and time each picture was taken.
Maybe even the local date and time, as well as the date and time back home.

First create a folder structure like this using YYYYMMDD format for the days:
~/website/2021/switzerland/20210818
~/website/2021/switzerland/20210820
~/website/2021/switzerland/20210821

Drag and drop the pictures you want to post into each day's folder

Create a csv file so you can title each day
~/website/2021/switzerland/tripreport.csv

Format of the csv file:
Date,Place
20210818,Geneva
20210820,Col du Grand Saint Bernard
20210821,Lac du Vieux Emosson

run this code to create the html

The only remaining task is to resize copies of the original pictures,
you don't want to post the pictures in their original size.
I haven't automated picture resizing since Irfanview Thumbnails does it so easily.
1. In Irfanview Thumbnails, navigate to each folder with pictures,
for example '~/website/2021/switzerland/20210818'.
2. Select all the files.
3. Right click, then start batch dialog with selected files...
4. In Batch conversion, Select Options.
5. Select Save quality lower than 100% - maybe try 95%.
6. Check Reset EXIF orientation tag - you don't want to expose your iphone's data to the world.
7. Select OK.
8. In Batch conversion, Select Advanced.
9. Check RESIZE:.
10. Enter Height: 1080 pixels - that's the height of a high def monitor or television.
11. Select Save files with original date/time.
12. Note there's an option Overwrite existing files, uncheck it for now though you'll
need check this to re-run the batch conversion.
12. Select OK.
13. In Batch conversion, Select Browse and browse to the output folder, for example
'~/website/2021/switzerland/'.
14. Select Start Batch.
The steps above sound much harder than they really are, nearly all of those selections are one time setup steps.

Where to host the html and pictures?
Buy a domain name, host dns for $0.50 / month on AWS Route53, create an s3 bucket, and publish it.
$18 / year for the domain name and route53 hosting, plus minimal storage and data transfer cost.

Known issues:
1. Assumes only one timezone.  If you take pictures at the airport, then fly somewhere on vacation
in another timezone and change your camera's time, the pictures from your home airport
will display with incorrect captions.  You'll need to manually edit those captions, but this
is trivial since those captions have both the correct (home) and incorrect (vacation) times display.
"""

import csv
import datetime
import exifread

# pip install exifread
import glob
import os

from collections import namedtuple
from operator import itemgetter

BASEFOLDER = "~//2021//switzerland//"

LOCATION = BASEFOLDER.split("//")[3].capitalize()
TITLE = LOCATION + " " + BASEFOLDER.split("//")[2]
CSVFILE = BASEFOLDER + "tripreport.csv"
HOME = "California"
OVERWRITE = 1
VACATIONOFFSET = -8


def tablestart(html):
    html.write('<table border="0" width="100%">\n')
    html.write("<tbody>\n")
    html.write("<tr>\n")
    return


def tableend(html):
    html.write("</tr>\n")
    html.write("</tbody>\n")
    html.write("</table>\n")
    return


def longdate(yyyymmdd):
    return "{}".format(
        (datetime.datetime.strptime(yyyymmdd, "%Y%m%d")).strftime("%A %B %e, %Y")
    )


def header(html, headertitle):
    html.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    html.write("<html>\n")
    html.write("<head>\n")
    html.write(
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1252"><title>{}</title>\n'.format(
            headertitle
        )
    )
    html.write('<link rel="stylesheet" href="../../dusty.css" type="text/css">\n')
    html.write("</head>\n")
    html.write("<body>\n")
    tablestart(html)
    html.write('<td width="33%"><a href="../../index.html">home</a></td>\n')
    html.write('<td width="34%"><h1>{}</h1></td>\n'.format(headertitle))
    html.write('<td width="33%"></td>\n')
    tableend(html)


def footer(html):
    html.write("</body>\n")
    html.write("</html>\n")


def navigation(html, index, lastday, navday, daytuple):
    tablestart(html)
    html.write('<td width="33%"><h5>')
    if not index:
        if min(trip) == navday:
            html.write('<a href="index.html">Previous</a><br>\n')
            html.write("Introduction")
        else:
            html.write(
                '<a href="{}.html">Previous</a><br>\n'.format(daytuple.previousday)
            )
            html.write("{}<br>\n".format(longdate(daytuple.previousday)))
            html.write("{}".format(daytuple.previouslocation))
    html.write("</h5><td>\n")
    if index:
        localday = ""
        localtitle = "Introduction"
    else:
        localday = longdate(navday)
        localtitle = daytuple.location
    html.write('<td width="34%"><h2>{}<br>\n'.format(localday))
    html.write("{}</h2></td>\n".format(localtitle))
    html.write('<td width="33%"><h6>')
    if index:
        localday = navday
        localtitle = daytuple.location
    else:
        localday = daytuple.nextday
        localtitle = daytuple.nextlocation
    if not lastday:
        html.write('<a href="{}.html">Next</a><br>\n'.format(localday))
        html.write("{}<br>\n".format(longdate(localday)))
        html.write("{}".format(localtitle))
    html.write("</h6><td>\n")
    tableend(html)
    return


if __name__ == "__main__":
    """
    we're creating a doubly linked list of days so
    each day knows the date and location of the prior and next days
    """
    with open(CSVFILE) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        trip = {}
        for day in reader:
            trip[day["Date"]] = day["Place"]
        forwardcsv = {}
        Day = namedtuple(
            "Day", "location previousday nextday previouslocation nextlocation"
        )
        for day in trip:
            if min(trip) == day:
                forwardcsv[day] = Day(trip[day], None, None, None, None)
            else:
                forwardcsv[day] = Day(
                    trip[day], previousday, None, previouslocation, None
                )
            previousday = day
            previouslocation = trip[day]
        trip = {}
        for day in reversed(forwardcsv):
            if max(forwardcsv) == day:
                trip[day] = Day(
                    forwardcsv[day].location,
                    forwardcsv[day].previousday,
                    None,
                    forwardcsv[day].previouslocation,
                    None,
                )
            else:
                trip[day] = Day(
                    forwardcsv[day].location,
                    forwardcsv[day].previousday,
                    nextday,
                    forwardcsv[day].previouslocation,
                    nextlocation,
                )
            nextday = day
            nextlocation = forwardcsv[day].location
        # create index.html
        index_html_path = BASEFOLDER + "index.html"
        if OVERWRITE or not os.path.exists(index_html_path):
            with open(index_html_path, "w") as index_html:
                for day in sorted(trip):
                    if min(trip) == day:
                        header(index_html, TITLE)
                        navigation(index_html, True, False, day, trip[day])
                        index_html.write("<br>\n")
                        firstday = day
                        firsttrip = trip[day]
                    index_html.write(
                        '<a href="{}.html">{} {}</a><br>\n'.format(
                            day, longdate(day), trip[day].location
                        )
                    )
                    if max(trip) == day:
                        index_html.write("<br>\n")
                        navigation(index_html, True, False, firstday, firsttrip)
                        footer(index_html)
        else:
            print("{} already exists, specify overwrite".format(index_html_path))
            exit(1)
        # create each day's html
        for day in trip:
            PICSFOLDER = BASEFOLDER + day + "//*"
            picfiles = filter(os.path.isfile, glob.glob(PICSFOLDER))
            pics = []
            html_file_path = BASEFOLDER + day + ".html"
            if OVERWRITE or not os.path.exists(html_file_path):
                for pic in picfiles:
                    if pic.endswith(
                        (
                            ".JPG",
                            ".jpg",
                            ".JPEG",
                            ".jpeg",
                            ".PNG",
                            ".png",
                            ".HEIC",
                            ".heic",
                        )
                    ):
                        filename = os.path.basename(pic)
                        with open(pic, "rb") as image:
                            # if we can't read the exif, use the time and date of the filename instead
                            exif = exifread.process_file(image)
                            try:
                                dt = str(exif["EXIF DateTimeOriginal"])
                            except KeyError:
                                print("no exif found for {}".format(filename))
                                dt = "{}".format(
                                    (
                                        datetime.datetime.fromtimestamp(
                                            os.path.getctime(pic)
                                        )
                                        + datetime.timedelta(hours=VACATIONOFFSET)
                                    ).strftime("%Y:%m:%d %H:%M:%S")
                                )
                            vacationtime = "{}".format(
                                (
                                    datetime.datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")
                                    + datetime.timedelta(0)
                                )
                                .strftime("%H:%M {} time")
                                .format(LOCATION)
                            )
                            hometime = "{}".format(
                                (
                                    datetime.datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")
                                    + datetime.timedelta(hours=VACATIONOFFSET)
                                )
                                .strftime("%H:%M {} time")
                                .format(HOME)
                            )
                            pics.append(
                                {
                                    "hometime": hometime,
                                    "vacationtime": vacationtime,
                                    "filename": filename,
                                }
                            )
                # create today's html with
                # a header,
                # top navigation,
                # today's pictures,
                # bottom navigation, and
                # a footer
                with open(html_file_path, "w") as html_file:
                    header(html_file, TITLE)
                    navigation(html_file, False, max(trip) == day, day, trip[day])
                    html_file.write("<br>\n")
                    for pic in sorted(pics, key=itemgetter("filename")):
                        html_file.write(
                            "{}{}{}\n".format(
                                '<img alt="" style="" src="', pic["filename"], '"><br>'
                            )
                        )
                        html_file.write("<br>\n")
                        html_file.write(
                            "{} {}<br>\n".format(pic["vacationtime"], pic["hometime"])
                        )
                        html_file.write("<br>\n")
                    navigation(html_file, False, max(trip) == day, day, trip[day])
                    footer(html_file)
            else:
                print("{} already exists, specify overwrite".format(html_file_path))
                exit(1)
