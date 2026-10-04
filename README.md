# <img src="./icon.png" width=20px> Libron

**Libron** is a modified version of [Readerly](https://github.com/nicoverbruggen/readerly) with various edits to give the font a more neutral look. 

The original font was imported and has been manually edited using [FontForge](https://fontforge.org). All modified source files are available in the `src` directory.

## Specimen

<img src="./specimen.svg" width=400px>

## General changes

Libron started as an attempt to make Readerly feel a little more appropriate for reading on e-readers. Some of the more expressive details that are part of Readerly stood out more than I wanted.

In particular, some of the serifs and capital forms seemed too distracting as I was reading.

What started as a few tweaks to the serifs to make the different font files a little more neutral has gradually developed into a broader reworking of Readerly's design:

- Many uppercase and lowercase letters, figures and punctuation marks have now been redrawn or refined across all four styles. 
- Spacing and kerning have been adjusted alongside the outlines to create a more even reading texture.
- Accented characters have been rebuilt where necessary, so that they remain consistent with their base glyphs.
- Synthetic small caps were added to the font, based on scaled down capitals for each four styles.

The result keeps Readerly's proportions and overall character, but has a calmer and more neutral appearance intended specifically for reading books. As such, it is a successor to Readerly.

## Building Libron

### Automatic builds

When a commit of Libron is tagged, a version is automatically released. The version number set in [VERSION](./VERSION) is used when building the font, and is embedded within the font.

The following variants are generated:

- Libron for desktop (`TTF`)
- Libron patched with [Nerd Fonts](https://www.nerdfonts.com) icons and Powerline glyphs (`TTF`), as family "Libron Nerd Font"
- Libron converted to a single advance width and patched the same way (`TTF`), as family "Libron Nerd Font Mono", for terminals
- Libron for [Kobo devices](https://github.com/nicoverbruggen/kobo-font-fix) (`KF TTF`)
- Libron's webfont variant (`WOFF2`) 

Libron for devices running CrossPoint Reader (`cpfont`) is built and published in [ebook-fonts](https://github.com/nicoverbruggen/ebook-fonts).

### Nerd Fonts variant

The patched fonts are built by `build.py --with-nerdfonts`, which runs the official [font-patcher](https://github.com/ryanoasis/nerd-fonts) (`--complete`) on the exported TTFs and writes the result to `out/nerd/`. The patcher version is pinned in [build.py](./build.py). `./local-build.sh` enables this by default; pass `--without-nerdfonts` to skip it.

Use `Libron Nerd Font` in your terminal or editor to get Powerline separators, Devicons, Font Awesome, Material Design and Codicons glyphs.

### Nerd Fonts mono variant

Libron is a proportional reading font, so a terminal needs a converted copy. `build.py --with-nerdfonts-mono` (also on by default in `./local-build.sh`) runs [scripts/make_mono.py](./scripts/make_mono.py) on the exported TTFs, then patches the result with `--single-width-glyphs`; the output is `out/nerd-mono/`, family "Libron Nerd Font Mono".

The conversion is mechanical, and deliberately so: every glyph is drawn into one `MONO_CELL_EM` cell (0.636em, DepartureMono Mono's), glyphs whose ink is wider than the cell are condensed to fit it, all ink is centred in the cell, and ASCII glyphs that would float (under `MONO_MIN_INK` of the cell) are widened, capped by `MONO_MAX_STRETCH` so punctuation does not turn into blobs. Kerning is dropped and hinting discarded, because the outlines move. A designer's monospace would redraw those glyphs instead of scaling them, so wide capitals end up lighter than a hand-drawn mono would be.

Use `Libron Nerd Font Mono` in a terminal (it is a real single-cell grid, and it also gains box drawing, block elements and braille, which the patcher only adds to monospaced sources). Keep the proportional "Libron Nerd Font" for UI and text.

### Building locally

You can run `./local-build.sh` if you have Podman installed to build the definitive fonts. If you have all dependencies installed locally, you can also use `./build.py` to build the font with Python.

## License

This font is available under the [OFL license](./LICENSE).
