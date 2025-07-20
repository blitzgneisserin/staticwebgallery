This is supposed to be a sophiticated static web gallery generator eventually.

[Example web site](https://simon-a.info/staticwebgallery/output/).

The “sophistication” about it right now: the Python script extracts with the help of exiftool metadata from the photos and displays the info automatically on the web site. So far, it extracts the keywords from the photos and creates a tag cloud of them, which you can see on the landing page. If you click on a tag, you see the thumbnails of the photos that contain that keyword/tag as metadata. Click on a thumbnail to see the big photo, under the photo you can see a caption which is also automatically created from the extracted metadata, it’s composed of the name of the city, the name of the state and the capture date (datetimeoriginal).

Of course, my plans are much much bigger: the whole project was inspired by the Wordpress plugin Media Library Assistant and it’s metadata mapping capabilities - but I wanted this as a static web site. Here is an [example of a gallery web site that uses Worpress/Media Library Assistant](https://gallery.simon-a.info/).

For all of this to work properly, of course the first step is to get the right metadata into your pictures, which you can do with Digikam, more precisely its tools GPS correlator and reverse geocoding - the latter creates actual location names from gps coordinates and saves them as metadata inside the photo.

Once the photos are ready, download this repo, put the photos into the directory "images", open a terminal, navigate into the directory where everything is and type:

python3 generate_gallery.py

At least that's how it works on Debian. Depending on the number of photos, a few seconds later you will find the whole website in the newly created directory "output" - now you can upload the contents of "output" to your website.
