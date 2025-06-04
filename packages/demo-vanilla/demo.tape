Output demo.gif

Require echo
Require just

Set Shell "fish"
Set FontSize 32
Set Width 1080
Set Height 1920
Set FontSize 48
Set FontFamily "JetBrainsMono Nerd Font"
Set Theme { "name": "SurrealDB", "black": "#15131D", "red": "#ef6487", "green": "#5eca89", "yellow": "#fdd877", "blue": "#65aef7", "magenta": "#FF00A0", "cyan": "#43c1be", "white": "#F9F9F9", "brightBlack": "#15131D", "brightRed": "#ef6487", "brightGreen": "#5eca89", "brightYellow": "#fdd877", "brightBlue": "#65aef7", "brightMagenta": "#aa7ff0", "brightCyan": "#43c1be", "brightWhite": "#F9F9F9", "background": "#29283b", "foreground": "#b3b0d6", "selection": "#3d3c58", "cursor": "#b3b0d6" }
Set MarginFill "#0E0C14"
Set BorderRadius 32
Set Margin 32
Set Padding 32
Set WindowBar Colorful
Set WindowBarSize 64
Set Framerate 20

# No need to activate venv if we call vhs already from within in
# Type "source .venv/bin/activate.fish"

Hide
Type "function fish_prompt; set_color ff00a0; echo -n '> '; set_color normal; end"
Enter
Type "clear"
Enter

Show
Type "uv run demo-vanilla query racing"
Sleep 500ms
Enter
Wait+Line@10s />/
Sleep 5s
