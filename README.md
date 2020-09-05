Size of Things
==============

This is a project to visualize various things - mostly space-type things, but not all - focusing on their relative size to one another.

It's heavily inspired by (and sources most of its images from) two similar efforts that I am deeply indebted to: J. Alllen Russell's now-retired [Starship Dimensions](http://www.merzo.net/indexSD.html) site, and Dirk Loechel's incredible [posters on DeviantArt](https://www.deviantart.com/dirkloechel/art/Size-Comparison-Science-Fiction-Spaceships-398790051).

This project takes those sources, as well as bits and bobs I've gathered elsewhere, and takes inspiration from the delightfully 70's [Powers of Ten](https://www.youtube.com/watch?v=0fKBhvDjuy0) video, in arranging them with the smallest items in the center,
and the largest on the edges, so you can zoom in and out and get a continuous stream of things at the given scale.

It turns out the hardest part of this project so far was programmatically distributing the ships around the field, for which I designed an algorithm that essentially creates a tightly-packed spiral of ships of increasing size. Currently this is done offline, as it is not terribly efficient in its current Python implementation.

If you have ships that you don't see represented, feel free to ping me to add them! Info on that can be found on the submit page (linked to in the lower-right-hand corner, or just read `submit.html`!)

Details
-------

This repository doesn't contain the images themselves, mostly because they're huge and not suited for a git repository. The metadata format should be pretty self-explanatory (just take a peek at any of the YAML files under `images`), so you can create your own version with whatever images you like.

The app depends on a `ships.json` file that is generated. To generate it, run `generate_index.py` - it will crawl through the `images` folder, gather up all the ships mentioned in the YAML files, and then place them according to their size. This might take a while - on my 10-year-old i7 2.6GHz Lenovo T530 it took about a minute and a half. It would be faster if it weren't in Python, but for now that's not a priority.
