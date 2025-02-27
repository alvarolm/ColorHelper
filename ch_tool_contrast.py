"""Color contrast tool."""
import sublime
import sublime_plugin
import mdpopups
from . import ch_util as util
from .ch_mixin import _ColorMixin
import copy
from . import ch_tools as tools

CONTRAST_DEMO = """
<div style="display: block; color: {}; background-color: {}; padding: 1em;">
<h2>Color Contrast</h2>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing<br>
elit, sed do eiusmod tempor incididunt ut labore et<br>
dolore magna aliqua. Ut enim ad minim veniam, quis<br>
nostrud exercitation ullamco laboris nisi ut aliquip<br>
ex ea commodo consequat.</p>
</div>
"""

DEF_RATIO = """---
markdown_extensions:
- markdown.extensions.attr_list
- markdown.extensions.def_list
- pymdownx.betterem
...

{}

## Format

<code>Color( / Color)?( ratio)?</code>

## Instructions

Colors should be within the sRGB gamut, any color<br>
that is not will have gamut reduction perfromed on it.

If only one color is provided, a default background<br>
of either **black** or **white** will be used.
"""


def parse_color(base, string, start=0, second=False):
    """
    Parse colors.

    The return of `more`:
    - `None`: there is no more colors to process
    - `True`: there are more colors to process
    - `False`: there are more colors to process, but we failed to find them.
    """

    length = len(string)
    more = None
    ratio = None
    # First color
    color = base.match(string, start=start, fullmatch=False)
    if color:
        start = color.end
        if color.end != length:
            more = True

            m = tools.RE_RATIO.match(string, start)
            if m:
                ratio = float(m.group(1))
                start = m.end(0)

            # Is the first color in the input or the second?
            if not second and not ratio:
                # Plus sign indicating we have an additional color to mix
                m = tools.RE_SLASH.match(string, start)
                if m and not ratio:
                    start = m.end(0)
                    more = start != length
                else:
                    more = False
            else:
                more = None if start == length else False

    if color:
        color.end = start
    return color, ratio, more


def evaluate(base, string):
    """Evaluate color."""

    colors = []

    try:
        color = string.strip()
        second = None
        ratio = None

        # Try to capture the color or the two colors to mix
        first, ratio, more = parse_color(base, color)
        if first and more is not None:
            if more is False:
                first = None
            else:
                second, ratio, more = parse_color(base, color, start=first.end, second=True)
                if not second or more is False:
                    first = None
                    second = None
            if first:
                first = first.color
            if second:
                second = second.color
        else:
            if first:
                first = first.color
                second = base("white" if first.luminance() < 0.5 else "black")

        # Package up the color, or the two reference colors along with the mixed.
        if first:
            colors.append(first.fit('srgb'))
        if second:
            if second[-1] < 1.0:
                second[-1] = 1.0
            colors.append(second.fit('srgb'))
            if ratio:
                if first[-1] < 1.0:
                    first = first.compose(second, space="srgb")
                hwb_fg = first.convert('hwb').clip()
                hwb_bg = second.convert('hwb').clip()
                first.update(hwb_fg)
                second.update(hwb_bg)

                colormod = util.import_color("ColorHelper.custom.st_colormod.Color")
                color = colormod(
                    "color({} min-contrast({} {}))".format(
                        hwb_fg.to_string(**util.FULL_PREC),
                        hwb_bg.to_string(**util.FULL_PREC),
                        ratio
                    )
                )
                first.update(base(color))
                colors[0] = first

            if first[-1] < 1.0:
                # Contrasted with current color
                colors.append(first.compose(second, space="srgb"))
                # Contrasted with the two extremes min and max
                colors.append(first.compose("white", space="srgb"))
                colors.append(first.compose("black", space="srgb"))
            else:
                colors.append(first)
    except Exception as e:
        print(e)
        colors = []
    return colors


class ColorHelperContrastRatioInputHandler(tools._ColorInputHandler):
    """Handle color inputs."""

    def __init__(self, view, initial=None, **kwargs):
        """Initialize."""

        self.color = initial
        super().__init__(view, **kwargs)

    def placeholder(self):
        """Placeholder."""

        return "Color"

    def initial_text(self):
        """Initial text."""

        if self.color is not None:
            return self.color
        elif len(self.view.sel()) == 1:
            self.setup_color_class()
            text = self.view.substr(self.view.sel()[0])
            if text:
                color = None
                try:
                    color = self.custom_color_class(text)
                    if color.space() not in self.filters:
                        raise ValueError('Space not in filters')
                except Exception:
                    pass
                if color is not None:
                    color = self.base(color)
                    return color.to_string(**util.DEFAULT)
        return ''

    def preview(self, text):
        """Preview."""

        style = self.get_html_style()

        try:
            colors = evaluate(self.base, text)
            html = mdpopups.md2html(self.view, DEF_RATIO.format(style))
            if len(colors) >= 3:
                lum2 = colors[1].luminance()
                lum3 = colors[2].luminance()
                if len(colors) > 3:
                    luma = colors[3].luminance()
                    lumb = colors[4].luminance()
                    mn = min(luma, lumb)
                    mx = max(luma, lumb)
                    min_max = "<ul><li><strong>min</strong>: {}</li><li><strong>max</strong>: {}</li></ul>".format(
                        mn, mx
                    )
                else:
                    min_max = ""
                html = (
                    "<p><strong>Fg</strong>: {}</p>"
                    "<p><strong>Bg</strong>: {}</p>"
                    "<p><strong>Relative Luminance (fg)</strong>: {}</p>{}"
                    "<p><strong>Relative Luminance (bg)</strong>: {}</p>"
                ).format(
                    colors[2].to_string(**util.DEFAULT),
                    colors[1].to_string(**util.DEFAULT),
                    lum3,
                    min_max,
                    lum2
                )
                html += "<p><strong>Contrast ratio</strong>: {}</p>".format(colors[1].contrast(colors[2]))
                html += CONTRAST_DEMO.format(
                    colors[2].convert('srgb').clip().to_string(**util.COMMA),
                    colors[1].convert('srgb').clip().to_string(**util.COMMA)
                )
            return sublime.Html(style + html)
        except Exception as e:
            print('huh?')
            print(e)
            return sublime.Html(mdpopups.md2html(self.view, DEF_RATIO.format(style)))

    def validate(self, color):
        """Validate."""

        try:
            colors = evaluate(self.base, color)
            return len(colors) > 0
        except Exception as e:
            print('what?')
            print(e)
            return False


class ColorHelperContrastRatioCommand(_ColorMixin, sublime_plugin.TextCommand):
    """Open edit a color directly."""

    def run(
        self, edit, color_helper_contrast_ratio, initial=None, on_done=None, **kwargs
    ):
        """Run command."""

        self.base = util.get_base_color()
        colors = evaluate(self.base, color_helper_contrast_ratio)
        color = None
        if colors:
            color = colors[0]

        if color is not None:
            if on_done is None:
                on_done = {
                    'command': 'color_helper',
                    'args': {'mode': "result", "result_type": "__tool__:__contrast__"}
                }
            call = on_done.get('command')
            if call is None:
                return
            args = copy.deepcopy(on_done.get('args', {}))
            args['color'] = color.to_string(**util.COLOR_FULL_PREC)
            self.view.run_command(call, args)

    def input(self, kwargs):  # noqa: A003
        """Input."""

        return ColorHelperContrastRatioInputHandler(self.view, **kwargs)
