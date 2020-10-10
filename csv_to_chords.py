#!/usr/bin/env python3
import os
import sys
import csv
import datetime
from diagram import MultiFingerChord
from bs4 import BeautifulSoup as bs
import yaml
import argparse

DEFAULT_STYLE = yaml.safe_load(open('config.yml'))

def parse_cmdline(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", help="path to CSV file defining chords")
    parser.add_argument("-c", "--colour", default=None, help="set a background colour for generated SVGs")
    parser.add_argument("-d", "--destdir", help="destination directory for chord diagrams")
    parser.add_argument("-f", "--force", action="store_true", default=False,
        help="force overwriting files in an existing destination directory")

    args = parser.parse_args(argv)
    # sanity checks go in here later

    return args


def symbolise(name):
    """
    replace pretend symbols with real ones (unicode ftw)
    """
    translations = {
            'b': '&#x266d;',
            '#': '&#x266f;',
            }
    tt = { ord(k): v for k, v in list(translations.items()) }

    return str(name).translate(tt)

def safe_name(chord):
    """
    Translate unsafe characters for filenames
    (on Linux, at least. May need more for windows)
    """
    transtable = {
            '#': '_sharp_',
            '/': '_on_',
            'b': '_flat_',
            '(': '_',
            ')': '_',
            }

    return chord.translate({ ord(k): v for k, v in transtable.items() })


def parse_csv(filename):
    """
    Expect the following fieldnames:
    title (aka name or chord)
    positions (aka frets)
    fingers (aka labels)
    barre (bool)
    extras (list of str (or list of dict))
    pn (position number)
    labelallfrets

    any unknown fields will be parsed as-is.

    """
    content = []
    with open(filename) as inf:
        reader = csv.DictReader(inf, restval=None, restkey='junk')
        for idx, chord in enumerate(reader):
            print(idx, chord)
            try:
                if not len(chord['extras'].strip()):
                    chord['extras'] = None
                else:
                    chord['extras'] = [ dict(zip(('string', 'fret', 'label'), chord['extras'].split(','))) ]

                has_barre = len(chord['barre'].strip()) > 0
                # filename wthout extension, in case we want to convert
                # do this first to avoid silly unicode chars in  filenames
                chord['index'] = idx + 1

                if has_barre:
                    chord['barre'] = min([ int(p) for p in chord['frets'] if p.isdigit() and int(p) > 0 ])
                else:
                    chord['barre'] = None

                chord['filename'] = safe_name('{index:03d}-{title}-variant_{variant}'.format(**chord))
                # use musical symbols where possible
                chord['label_all'] = chord['label_all'].strip().lower() == 'y'

            except KeyError as E:
                print(E, chord)
                raise
                continue

            content.append(chord)
            content.append(reverse_chord(chord))

    return content

def reverse_chord(achord):
    """
    reverse frets, labels and extras to make LH from RH (or vice versa)

    Args:
        achord(dict): dicitonary representing a chord
    """
    # work on a shallow copy of the dict
    revchord = achord.copy()
    if '-' in  revchord['frets']:
        revchord['frets'] = revchord['frets'].split('-')
    else:
        revchord['frets'] = list(revchord['frets'])
    revchord['fingers'] = list(revchord['fingers'])

    revchord['frets'].reverse()
    revchord['fingers'].reverse()
    if revchord.get('extras') is not None:
        for e in revchord['extras']:
            e['string'] = abs(int(e['string']) - 3 )
    revchord['filename'] = "{filename}-lh".format(**revchord)

    return revchord


if __name__ == '__main__':
    opts = parse_cmdline(sys.argv[1:])

    chorddefs = parse_csv(opts.csvfile)
    if opts.destdir:
        outdir = opts.destdir
    else:
        outdir = '/tmp/chords_{:%Y-%m-%d-%H.%M.%S}'.format(datetime.datetime.now())

    try:
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        else:
            if not opts.force:
                print("not overwriting files in destination directory {}, use --force to, well, force this  to happen".format(outdir))
                sys.exit(0)
    except (IOError, OSError) as E:
        raise()

    if opts.colour:
        DEFAULT_STYLE['drawing']['background_color'] = opts.colour


    for c in chorddefs:
        if len(c['frets']) == 0:
            continue
        try:
            crd = MultiFingerChord(style=DEFAULT_STYLE, positions=c['frets'], **c)
            dest = os.path.join(outdir, '{filename}.svg'.format(**c))
            if os.path.exists(dest):
                print("dest already exists, timestamping")
                dest = '{}-{}'.format(dest, datetime.datetime.now().timestamp())
            crd.save(dest)
        except:
            print(c)
            print(crd)
            raise()
            sys.exit(1)

# this is what lobo gave us

# title,positions,fingers,pn,variant,barre,extras,labelallfrets
# C,0003,---3,,C,,,
# C,0003,---4,,C2,,,



