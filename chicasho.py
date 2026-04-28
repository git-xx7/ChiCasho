import random
import time
import turtle

def load_game_data(filepath = "game_data.txt"):
    config = {}
    win_rules = {}
    locations = []
    current_section = None
    current_location = None
    current_option = None

    with open(filepath, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            
            if line == "[CONFIG]":
                current_section = "config"
                current_location = None
                current_option = None
            elif line == "[WIN_RULES]":
                current_section = "win_rules"
                current_location = None
                current_option = None
            elif line == "[LOCATION]":
                current_section = "location"
                current_location = {"options": []}
                locations.append(current_location)
                current_option = None
            elif line == "[OPTION]":
                current_option = {}
                if current_location is not None:
                    current_location["options"].append(current_option)
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    value = int(value)
                except ValueError:
                    pass
                if current_section == "config":
                    config[key] = value
                elif current_section == "win_rules":
                    win_rules[key] = value
                elif current_option is not None:
                    current_option[key] = value
                elif current_location is not None:
                    current_location[key] = value
    return config, win_rules, locations

'''
load the game data
'''
try:
    config, win_rules, locations = load_game_data("game_data.txt")
except FileNotFoundError:
    print("ERROR: game_data.txt not found.")
    turtle.bye()

'''
Constants
'''
SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]
MAP_PATH = config["MAP_PATH"]
MAX_TURNS = config["MAX_TURNS"]
START_CASH = config["START_CASH"]
START_STABILITY = config["START_STABILITY"]

TITLE_COLORS = ["#facc15", "#fb7185", "#38bdf8", "#34d399", "#f97316"]
DICE_FACES = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

'''
Screen Setup
'''
screen = turtle.Screen()
screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
screen.title("Chicasho: A Financial Adventure")
screen.bgcolor("#050816")
screen.colormode(255)
screen.tracer(0)

'''
Turtle Pens
'''
title_pen = turtle.Turtle()
title_pen.hideturtle()
title_pen.penup()
title_pen.speed(0)

ui_pen = turtle.Turtle()
ui_pen.hideturtle()
ui_pen.penup()
ui_pen.speed(0)

map_pen = turtle.Turtle()
map_pen.hideturtle()
map_pen.penup()
map_pen.speed(0)

story_pen = turtle.Turtle()
story_pen.hideturtle()
story_pen.penup()
story_pen.speed(0)

player = turtle.Turtle()
player.shape("turtle")
player.color("#22c55e")
player.shapesize(1.4, 1.4)
player.penup()
player.speed(0)
player.hideturtle()

'''
Game State
'''
game_state = {
    "phase": "welcome",
    "player_name": "Player",
    "cash": START_CASH,
    "score": 0,
    "stability": START_STABILITY,
    "position": 0,
    "turn": 1,
    "max_turns": MAX_TURNS,
    "last_roll": 0,
    "status_message": "Click to begin.",
    "popup_active": False,
    "awaiting_choice": False,
    "is_rolling": False,
    "game_over": False,
    "title_frame": 0,
    "start_pulse": 0,
}

popup_buttons = []
current_location = None

'''
Helper Functions
'''
def play_sound(sound_file):
    pass

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))

def point_in_box(x, y, box):
    left = min(box["x1"], box["x2"])
    right = max(box["x1"], box["x2"])
    bottom = min(box["y1"], box["y2"])
    top = max(box["y1"], box["y2"])
    return left <= x <= right and bottom <= y <= top

def format_money(amount):
    sign = "+" if amount > 0 else ""
    return f"{sign}${amount}"

def net_worth():
    return game_state["cash"] + game_state["score"] * 25 + game_state["stability"] * 8

def wrap_text(text, max_chars = 52):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " + word if current else word)
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def save_game_report():
    with open("game_report.txt", "w") as f:
        f.write("===CHICASHO GAME REPORT===\n")
        f.write(f"Player: {game_state['player_name']}\n")
        f.write(f"Cash: ${game_state['cash']}\n")
        f.write(f"Score: {game_state['score']}\n")
        f.write(f"Stability: {game_state['stability']}\n")
        f.write(f"Net Worth: ${net_worth()}\n")
        f.write(f"Turns: {game_state['turn'] - 1} / {MAX_TURNS}\n")
        result = "WIN" if net_worth() >= win_rules["net_worth_goal"] else "LOSS"
        f.write(f"Result: {result}\n")
        f.write(f"--------x--------\n")

'''
Drawing Functions
'''
def draw_rectangle(pen, x1, y1, x2, y2, fill, outline, pensize=1):
    pen.goto(x1, y1)
    pen.setheading(0)
    pen.pensize(pensize)
    pen.color(outline)
    pen.fillcolor(fill)
    pen.begin_fill()
    pen.pendown()
    for _ in range(2):
        pen.forward(x2 - x1)
        pen.right(90)
        pen.forward(y1 - y2)
        pen.right(90)
    pen.end_fill()
    pen.penup()

def draw_map_overlay():
    map_pen.clear()
    map_pen.pensize(4)
    map_pen.color("#0ea5e9")

    for index, location in enumerate(locations):
        next_location = locations[(index + 1) % len(locations)]
        map_pen.goto(location["x"], location["y"])
        map_pen.pendown()
        map_pen.goto(next_location["x"], next_location["y"])
        map_pen.penup()

    for index, location in enumerate(locations):
        map_pen.goto(location["x"], location["y"])
        map_pen.dot(30, "#0f172a")
        highlight = "#facc15" if index == game_state["position"] and game_state["phase"] == "playing" else "#38bdf8"
        map_pen.dot(20, highlight)
        map_pen.goto(location["x"], location["y"] - 26)
        map_pen.color("#111827")
        map_pen.write(location["name"], align="center", font=("Arial", 8, "bold"))

def draw_sidebar():
    draw_rectangle(ui_pen, 350, 395, 535, -395, "#0f172a", "#38bdf8", 2)

    ui_pen.goto(442, 340)
    ui_pen.color("#f8fafc")
    ui_pen.write("CHICASHO", align="center", font=("Courier", 18, "bold"))

    info_lines = [
        f"Player: {game_state['player_name']}",
        f"Cash: ${game_state['cash']}",
        f"Score: {game_state['score']}",
        f"Stability: {game_state['stability']}/100",
        f"Turn: {game_state['turn']}/{game_state['max_turns']}",
        f"Last Roll: {game_state['last_roll']}",
    ]

    y = 285
    for line in info_lines:
        ui_pen.goto(442, y)
        ui_pen.color("#dbeafe")
        ui_pen.write(line, align="center", font=("Arial", 11, "normal"))
        y -= 34

    ui_pen.goto(442, 50)
    ui_pen.color("#facc15")
    ui_pen.write("WIN GOAL", align="center", font=("Courier", 14, "bold"))

    rules = [
        "Survive all 10 turns",
        "Stay above -$50 cash",
        "Keep stability above 5",
        "Finish with net worth 2250+",
    ]
    y = 12
    for line in rules:
        ui_pen.goto(442, y)
        ui_pen.color("#cbd5e1")
        ui_pen.write(line, align="center", font=("Arial", 10, "normal"))
        y -= 24

    draw_rectangle(ui_pen, 370, -205, 515, -265, "#f59e0b", "#fde68a", 2)
    ui_pen.goto(442, -247)
    ui_pen.color("#111827")
    ui_pen.write("ROLL DICE", align="center", font=("Courier", 16, "bold"))

    status_lines = wrap_text(game_state["status_message"], max_chars=22)
    status_y = -310
    for line in status_lines:
        ui_pen.goto(442, status_y)
        ui_pen.color("#93c5fd")
        ui_pen.write(line, align="center", font=("Arial", 10, "normal"))
        status_y -= 20

def draw_game_scene():
    title_pen.clear()
    ui_pen.clear()
    story_pen.clear()
    screen.bgcolor("#d9dde6")
    try:
        screen.bgpic(MAP_PATH)
    except turtle.TurtleGraphicsError:
        screen.bgpic("")

    draw_map_overlay()
    draw_sidebar()
    player.showturtle()
    current = locations[game_state["position"]]
    player.goto(current["x"], current ["y"] + 60)
    screen.update()

'''
Title Screen
'''
def animate_title():
    if game_state["phase"] != "welcome":
        return
    
    frame = game_state["title_frame"]
    color = TITLE_COLORS[frame % len(TITLE_COLORS)]
    wobble = (frame % 6) - 3
    shadow_shift = 4 if frame % 2 == 0 else 6

    title_pen.clear()
    screen.bgcolor("#050816")
    screen.bgpic("")

    draw_rectangle(title_pen, -380, 245, 380, -210, "#0b1120", "#facc15", 3)

    title_pen.goto(4, 124 - shadow_shift)
    title_pen.color("#0ea5e9")
    title_pen.write("CHICASHO", align="center", font=("Courier", 60, "bold"))

    title_pen.goto(0, 132 + wobble)
    title_pen.color(color)
    title_pen.write("CHICASHO", align="center", font=("Courier", 60, "bold"))

    title_pen.goto(0, 56)
    title_pen.color("#e2e8f0")
    title_pen.write("A Financial Adventure", align="center", font=("Courier", 22, "bold"))

    lines = [
        "Roll across Chicago. Make smart money choices.",
        "Every stop gives you two options with real tradeoffs.",
        "Reach the end with strong cash, score, and stability.",
    ]
    y = -5
    for line in lines:
        title_pen.goto(0, y)
        title_pen.color("#cbd5e1")
        title_pen.write(line, align="center", font=("Arial", 13, "normal"))
        y -= 38

    pulse_colors = ["#34d399", "#facc15", "#ffffff", "#facc15"]
    pulse_sizes = [18, 20, 22, 20]
    pulse_index = game_state["start_pulse"] % len(pulse_colors)

    title_pen.goto(0, -150)
    title_pen.color(pulse_colors[pulse_index])
    title_pen.write(
        "[CLICK ANYWHERE TO START]",
        align="center",
        font=("Courier", pulse_sizes[pulse_index], "bold")
    )

    game_state["start_pulse"] += 1
    screen.update()
    game_state["title_frame"] += 1
    screen.ontimer(animate_title, 180)

'''
Popup Functions
'''
def ask_player_name():
    name = screen.textinput("Chicasho", "Enter yout player name:")
    if name and name.strip():
        game_state["player_name"] = name.strip()

def clear_popup():
    global popup_buttons
    popup_buttons = []
    story_pen.clear()
    game_state["popup_active"] = False 
    game_state["awaiting_choice"] = False 

def draw_popup_button(x1, y1, x2, y2, fill, outline, label, action, text_color="#0f172a"):
    draw_rectangle(story_pen, x1, y1, x2, y2, fill, outline, 2)
    story_pen.goto((x1 + x2) / 2, y2 + 14)
    story_pen.color(text_color)
    story_pen.write(label, align="center", font=("Courier", 11, "bold"))
    popup_buttons.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "action": action})

def show_choice_popup(location):
    clear_popup()
    game_state["popup_active"] = True
    game_state["awaiting_choice"] = True

    draw_rectangle(story_pen, -325, 250, 235, -135, "#0f172a", "#facc15", 3)
    
    story_pen.goto(-45, 192)
    story_pen.color("#f8fafc")
    story_pen.write(location["name"], align="center", font=("Courier", 18, "bold"))

    story_pen.goto(-45, 145)
    story_pen.color("#93c5fd")
    desc_lines = wrap_text(location["description"])
    desc_y = 155
    for line in desc_lines:
        story_pen.goto(-45, desc_y)
        story_pen.color("#93c5fd")
        story_pen.write(line, align="center", font=("Arial", 11, "normal"))
        desc_y -= 24
    story_pen.goto(-45, 82)
    story_pen.color("#cbd5e1")
        
    option_a = location["options"][0]
    option_b = location["options"][1]

    draw_popup_button(-285, 35, 195, -25, "#38bdf8", "#bae6fd", option_a["label"], ("choice", 0))
    draw_popup_button(-285, -40, 195, -100, "#fb7185", "#fecdd3", option_b["label"], ("choice", 1))

    screen.update()

def show_turn_summary(location_name, choice, cash_delta, score_delta, stability_delta):
    clear_popup()
    game_state["popup_active"] = True
    draw_rectangle(story_pen, -325, 250, 235, -135, "#111827", "#34d399", 3)

    story_pen.goto(-45, 205)
    story_pen.color("#34d399")
    story_pen.write("TURN RESULT", align="center", font=("Courier", 16, "bold"))

    story_pen.goto(-45, 170)
    story_pen.color("#e5e7eb")
    story_pen.write(f"Stop: {location_name}", align="center", font=("Arial", 11, "normal"))

    story_pen.goto(-45, 145)
    story_pen.write(f"Choice: {choice['label']}", align="center", font=("Arial", 11, "normal"))

    # Wrap the result text
    result_lines = wrap_text(choice["result"], max_chars=52)
    result_y = 118
    for line in result_lines:
        story_pen.goto(-45, result_y)
        story_pen.color("#93c5fd")
        story_pen.write(line, align="center", font=("Arial", 10, "italic"))
        result_y -= 20

    # Stats below result
    stats = [
        f"Cash:       {format_money(cash_delta)}",
        f"Score:      {score_delta:+d}",
        f"Stability:  {stability_delta:+d}",
        f"Net Worth:  ${net_worth()}",
    ]
    stat_y = result_y - 10
    for line in stats:
        story_pen.goto(-45, stat_y)
        story_pen.color("#e5e7eb")
        story_pen.write(line, align="center", font=("Courier", 10, "normal"))
        stat_y -= 26

    draw_popup_button(-135, -125, 45, -175, "#facc15", "#fde68a", "CONTINUE", ("continue", None))
    screen.update()

def show_end_screen(win, reason):
    clear_popup()
    game_state["phase"] = "end"
    game_state["game_over"] = True
    title_pen.clear()
    ui_pen.clear()
    map_pen.clear()
    player.hideturtle()
    screen.bgpic("")
    screen.bgcolor("#050816")

    accent = "#22c55e" if win else "#ef4444"
    title = "YOU WIN" if win else "GAME OVER"

    draw_rectangle(ui_pen, -360, 250, 360, -220, "#0b1120", accent, 3)
    ui_pen.goto(0, 160)
    ui_pen.color(accent)
    ui_pen.write(title, align="center", font=("Courier", 32, "bold"))

    lines = [
        reason,
        f"Cash: ${game_state['cash']}",
        f"Score: {game_state['score']}",
        f"Stability: {game_state['stability']}",
        f"Final Net Worth: ${net_worth()}",
        "Click anywhere to close.",
    ]
    y = 90
    for line in lines:
        ui_pen.goto(0, y)
        ui_pen.color("#e2e8f0")
        ui_pen.write(line, align="center", font=("Arial", 14, "normal"))
        y -= 48

    screen.update()

'''
Game Flow
'''
def animate_dice():
    glow_colors = ["#38bdf8", "#facc15", "#ffffff", "#facc15"]

    for i in range(12):
        roll = random.randint(1, 6)
        glow = glow_colors[i % len(glow_colors)]

        draw_rectangle(ui_pen, 382, -112, 502, -196, glow, glow, 3)
        draw_rectangle(ui_pen, 388, -118, 496, -190, "#111827", "#93c5fd", 2)

        ui_pen.goto(442, -184)
        ui_pen.color("#f8fafc")
        ui_pen.write(DICE_FACES[roll], align="center", font=("Courier", 34, "bold"))

        screen.update()
        time.sleep(0.09)

def move_player(steps):
    for _ in range(steps):
        game_state["position"] = (game_state["position"] + 1) % len(locations)
        current = locations[game_state["position"]]
        draw_game_scene()
        player.goto(current["x"], current["y"] + 34)
        screen.update()
        time.sleep(0.36)

def start_turn(roll):
    global current_location
    game_state["last_roll"] = roll 
    move_player(roll)
    current_location = locations[game_state["position"]]
    game_state["status_message"] = f"You landed on {current_location['name']}."
    draw_game_scene()
    show_choice_popup(current_location)

def apply_choice(choice_index):
    choice = current_location["options"][choice_index]
    game_state["cash"] += choice["cash"]
    game_state["score"] += choice["score"]
    game_state["stability"] = clamp(game_state["stability"] + choice["stability"], 0, 100)
    game_state["status_message"] = choice["result"]
    draw_game_scene()
    show_turn_summary(
        current_location["name"],
        choice,
        choice["cash"],
        choice["score"],
        choice["stability"]
    )

def finish_turn():
    game_state["turn"] += 1
    game_state["is_rolling"] = False
    clear_popup()

    if game_state["cash"] < -50:
        show_end_screen(False, "You fell too far into debt before the final turn.")
        return

    if game_state["stability"] <= 5:
        show_end_screen(False, "Your stability crashed before you reached the end.")
        return

    if game_state["turn"] > game_state["max_turns"]:
        if net_worth() >= 2250:
            show_end_screen(True, "You completed the full Chicago run with strong finances.")
        else:
            show_end_screen(False, "You made it to the end, but your finances were not strong enough to win.")
        return

    game_state["status_message"] = "Turn complete. Roll again."
    draw_game_scene()

def begin_game():
    game_state["phase"] = "playing"
    game_state["status_message"] = "Roll the dice to begin your route."
    ask_player_name()
    draw_game_scene()

'''
Click Handler
'''
def handle_click(x,y):
    if game_state["phase"] == "welcome":
        begin_game()
        return
    
    if game_state["game_over"]:
        turtle.bye()
        return

    if game_state["popup_active"]:
        for button in popup_buttons:
            if point_in_box(x, y, button):
                action, value = button["action"]
                if action == "choice":
                    apply_choice(value)
                    return
                if action == "continue":
                    finish_turn()
                    return 

        return

    if 370 <= x <= 515 and -265 <= y <= -205 and not game_state["is_rolling"]:
        game_state["is_rolling"] = True
        game_state["status_message"] = "Rolling the dice..."
        draw_game_scene()
        animate_dice()
        roll = random.randint(1, 6)
        draw_game_scene()
        draw_rectangle(ui_pen, 382, -112, 502, -196, "#facc15", "#facc15", 3)
        draw_rectangle(ui_pen, 388, -118, 496, -190, "#111827", "#ffffff", 2)
        ui_pen.goto(442, -184)
        ui_pen.color("#f8fafc")
        ui_pen.write(DICE_FACES[roll], align="center", font=("Courier", 38, "bold"))
        screen.update()
        screen.ontimer(lambda: start_turn(roll), 700)

'''
Start the Game 
'''
animate_title()
screen.onclick(handle_click)
screen.listen()
turtle.done()
