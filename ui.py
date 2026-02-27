import pygame


class StatusBar:
    def __init__(self, x, y, w, h, label, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.font = font
        self.bg_color = (44, 62, 80)      # Sophisticated dark blue-gray
        self.border_color = (189, 195, 199) # Light gray border
        self.radius = 8

    def draw(self, screen, value):
        # Draw background container
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=self.radius)
        
        # Determine bar color
        if self.label == 'Stress' or self.label == 'Hunger':
            # Red if high
            bar_color = (231, 76, 60) if value > 70 else (46, 204, 113)
        else:
            # Red if low status
            bar_color = (231, 76, 60) if value < 30 else (46, 204, 113)

        # Draw fill
        fill_width = int(self.rect.width * value / 100)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(screen, bar_color, fill_rect, border_radius=self.radius)

        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=self.radius)

        # Draw label
        text = self.font.render(f"{self.label}: {int(value)}", True, (236, 240, 241))
        screen.blit(text, (self.rect.x, self.rect.y - 28))


class Button:
    def __init__(self, x, y, w, h, text, font, enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.enabled = enabled
        self.base_color = (52, 152, 219)    # Bright blue
        self.hover_color = (41, 128, 185)   # Darker blue
        self.disabled_color = (127, 140, 141) # Gray
        self.border_color = (236, 240, 241) # Off-white
        self.radius = 10

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)

        if not self.enabled:
            color = self.disabled_color
            txt_color = (189, 195, 199)
        elif is_hovered:
            color = self.hover_color
            txt_color = (255, 255, 255)
        else:
            color = self.base_color
            txt_color = (255, 255, 255)

        # Draw main button
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=self.radius)

        txt = self.font.render(self.text, True, txt_color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


def _hours_to_hhmm(hours: float) -> str:
    total_minutes = round(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}:{m:02d}"


class InputBox:
    # Field indices
    FIELD_H = 0
    FIELD_M = 1

    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.prompt_text = ""
        self.active = False
        self._h_text = ""        # hours digits (up to 2)
        self._m_text = ""        # minutes digits (exactly 2)
        self._focus = self.FIELD_H   # which field is active
        self.result = None
        self._action_name = ""
        self.max_hours = 99.0
        self._error = ""

        # Course selection for study
        self.courses = []
        self.selected_course = None
        self._course_rects = []


    def open(self, action_name, max_hours: float = 99.0, courses=None):
        self.active = True
        self._h_text = ""
        self._m_text = ""
        self._focus = self.FIELD_H
        self.result = None
        self._error = ""
        self._action_name = action_name
        self.max_hours = max_hours
        self.courses = courses or []
        self.selected_course = None
        self._course_rects = []
        
        max_str = _hours_to_hhmm(max_hours)
        self.prompt_text = f"How long to {action_name}? (max {max_str})"


    def _total_hours(self) -> float | None:
        if not self._h_text:
            return None
        h = int(self._h_text)
        m = int(self._m_text) if self._m_text else 0
        if m >= 60:
            return None
        return h + m / 60.0


    def handle_event(self, event):
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                self._error = ""
                return None

            if event.key == pygame.K_RETURN:
                return self._try_confirm()

            if event.key == pygame.K_BACKSPACE:
                self._error = ""
                if self._focus == self.FIELD_H:
                    self._h_text = self._h_text[:-1]
                else:
                    if self._m_text:
                        self._m_text = self._m_text[:-1]
                    else:
                        # backspace from empty minutes → jump back to hours
                        self._focus = self.FIELD_H

            elif event.key == pygame.K_TAB:
                # Toggle between fields
                self._focus = self.FIELD_M if self._focus == self.FIELD_H else self.FIELD_H
                self._error = ""

            elif event.unicode.isdigit():
                self._error = ""
                self._type_digit(event.unicode)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            if self.h_rect.collidepoint(mouse_pos):
                self._focus = self.FIELD_H
                self._error = ""
            
            elif self.m_rect.collidepoint(mouse_pos):
                self._focus = self.FIELD_M
                self._error = ""

            # Check course selection
            for i, rect in enumerate(self._course_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_course = self.courses[i]
                    self._error = ""

        return None

    def _type_digit(self, ch: str):
        if self._focus == self.FIELD_H:
            if len(self._h_text) < 2:
                self._h_text += ch
                # Auto-jump: if we already have 2 hour digits, move to minutes
                if len(self._h_text) == 2:
                    self._focus = self.FIELD_M
        else:
            if len(self._m_text) < 2:
                self._m_text += ch
        return None

    def _try_confirm(self):
        if self._action_name == 'study' and not self.selected_course:
            self._error = "Please select a course to study"
            return None

        value = self._total_hours()
        if value is None or value <= 0:
            self._error = "Enter a valid time greater than 0"
            return None
        m = int(self._m_text) if self._m_text else 0
        if m >= 60:
            self._error = "Minutes must be 0-59"
            return None
        if value > self.max_hours + 1e-9:
            self._error = f"Max allowed: {_hours_to_hhmm(self.max_hours)}"
            return None
        
        # Return hours AND selected course for study
        self.result = (value, self.selected_course) if self._action_name == 'study' else value
        self.active = False
        self._error = ""
        return self.result


    def draw(self, screen):
        if not self.active:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Dynamic height if courses are shown
        base_h = 170
        extra_h = (len(self.courses) * 35 + 40) if self.courses else 0
        box_w, box_h = 420, base_h + extra_h
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 2, border_radius=10)

        # Prompt
        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 18))

        # Two input fields
        field_y = box_y + 58
        field_h = 44

        # Hours field
        self.h_rect = pygame.Rect(box_x + 20, field_y, 110, field_h)
        h_active = self._focus == self.FIELD_H
        h_border_color = (255, 220, 80) if h_active else (140, 140, 200)
        pygame.draw.rect(screen, (55, 55, 80), self.h_rect, border_radius=6)
        pygame.draw.rect(screen, h_border_color, self.h_rect, 2, border_radius=6)

        if not self._h_text:
            ph = self.font.render("HH", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=self.h_rect.center))
        else:
            h_surf = self.font.render(self._h_text, True, (255, 255, 255))
            screen.blit(h_surf, h_surf.get_rect(center=self.h_rect.center))

        # Colon separator
        colon_surf = self.font.render(":", True, (200, 200, 200))
        colon_x = box_x + 20 + 110 + 10
        screen.blit(colon_surf, colon_surf.get_rect(centery=field_y + field_h // 2, x=colon_x))

        # Minutes field
        self.m_rect = pygame.Rect(colon_x + 22, field_y, 110, field_h)
        m_active = self._focus == self.FIELD_M
        m_border_color = (255, 220, 80) if m_active else (140, 140, 200)
        pygame.draw.rect(screen, (55, 55, 80), self.m_rect, border_radius=6)
        pygame.draw.rect(screen, m_border_color, self.m_rect, 2, border_radius=6)

        if not self._m_text:
            ph = self.font.render("MM", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=self.m_rect.center))
        else:
            m_surf = self.font.render(self._m_text, True, (255, 255, 255))
            screen.blit(m_surf, m_surf.get_rect(center=self.m_rect.center))

        # Course Selection Area
        if self.courses:
            self._course_rects = []
            list_y = field_y + field_h + 45
            header = self.smallfont.render("Select Course to Study:", True, (200, 200, 255))
            screen.blit(header, (box_x + 20, list_y - 25))
            
            for i, c in enumerate(self.courses):
                rect = pygame.Rect(box_x + 20, list_y + i*35, box_w - 40, 30)
                self._course_rects.append(rect)
                
                is_sel = (c == self.selected_course)
                bg = (70, 70, 120) if is_sel else (50, 50, 70)
                border = (255, 255, 150) if is_sel else (100, 100, 150)
                
                pygame.draw.rect(screen, bg, rect, border_radius=5)
                pygame.draw.rect(screen, border, rect, 1 if not is_sel else 2, border_radius=5)
                
                txt = self.smallfont.render(f"{c.name} ({c.knowledge:.1f}%)", True, (255, 255, 255))
                screen.blit(txt, (rect.x + 10, rect.y + (rect.height - txt.get_height()) // 2))

        # Error or hint
        msg_y = box_y + box_h - 30
        if self._error:
            err_surf = self.smallfont.render(self._error, True, (255, 100, 100))
            screen.blit(err_surf, (box_x + 20, msg_y))
        else:
            hint = "Enter: Confirm    Esc: Cancel    Click to Select Course"
            hint_surf = self.smallfont.render(hint, True, (140, 140, 180))
            screen.blit(hint_surf, (box_x + 20, msg_y))


class NumberBox:
    def __init__(self, font, smallfont, is_float=False):
        self.font = font
        self.smallfont = smallfont
        self.active = False
        self.prompt_text = ""
        self._text = ""
        self.result = None
        self._error = ""
        self._max = 999
        self.is_float = is_float

    def open(self, prompt: str, max_value: float = 999):
        self.active = True
        self._text = ""
        self.result = None
        self._error = ""
        self._max = max_value
        self.prompt_text = prompt

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                self._error = ""
                return None
            elif event.key == pygame.K_RETURN:
                if not self._text:
                    self._error = "Enter a number first"
                    return None
                try:
                    val = float(self._text) if self.is_float else int(self._text)
                    if val <= 0:
                        self._error = "Must be at least 0.1" if self.is_float else "Must be at least 1"
                    elif val > self._max:
                        self._error = f"Max is {self._max}"
                    else:
                        self.result = val
                        self.active = False
                        self._error = ""
                        return self.result
                except ValueError:
                    self._error = "Invalid number"
                    return None
            elif event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                self._error = ""
            elif event.unicode.isdigit():
                if len(self._text) < 5:
                    self._text += event.unicode
                    self._error = ""
            elif self.is_float and event.unicode == "." and "." not in self._text:
                if len(self._text) < 5:
                    self._text += "."
                    self._error = ""
        return None

    def draw(self, screen):
        if not self.active:
            return
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 360, 150
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, (40, 40, 60), box_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 2, border_radius=10)

        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (box_x + 20, box_y + 18))

        field_rect = pygame.Rect(box_x + 20, box_y + 58, box_w - 40, 44)
        pygame.draw.rect(screen, (55, 55, 80), field_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 220, 80), field_rect, 2, border_radius=6)

        if self._text:
            val_surf = self.font.render(self._text, True, (255, 255, 255))
            screen.blit(val_surf, val_surf.get_rect(center=field_rect.center))
        else:
            ph = self.font.render("0", True, (100, 100, 130))
            screen.blit(ph, ph.get_rect(center=field_rect.center))

        if self._error:
            err_surf = self.font.render(self._error, True, (255, 100, 100))
            screen.blit(err_surf, (box_x + 20, box_y + 112))
        else:
            hint_surf = self.smallfont.render("Enter to confirm    Esc to cancel", True, (140, 140, 180))
            screen.blit(hint_surf, (box_x + 20, box_y + 118))


class AlertBox:
    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.active = False
        self.title = ""
        self.body = ""
        self.color_type = "red"  # "red" or "yellow"
        
        # Color themes
        self._themes = {
            "red": {
                "bg": (60, 20, 20),
                "border": (255, 80, 80),
                "title": (255, 80, 80),
                "btn": (180, 40, 40),
                "btn_border": (255, 120, 120)
            },
            "yellow": {
                "bg": (60, 60, 20),
                "border": (255, 220, 0),
                "title": (255, 220, 0),
                "btn": (180, 160, 40),
                "btn_border": (255, 230, 120)
            }
        }

    def open(self, title: str, body: str, color_type: str = "red"):
        self.active = True
        self.title = title
        self.body = body
        self.color_type = color_type if color_type in self._themes else "red"

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.active = False
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, '_btn_rect') and self._btn_rect.collidepoint(event.pos):
                self.active = False
                return True
        return None

    def draw(self, screen):
        if not self.active:
            return

        theme = self._themes[self.color_type]

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 540, 220 
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, theme["bg"], box_rect, border_radius=10)
        pygame.draw.rect(screen, theme["border"], box_rect, 2, border_radius=10)

        # Title 
        title_surf = self.font.render(self.title, True, theme["title"])
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_y + 20))

        # Body  (split into lines for multi-line support)
        lines = self.body.split('\n')
        line_height = 28 
        for i, line in enumerate(lines):
            body_surf = self.smallfont.render(line.strip(), True, (240, 240, 240))
            screen.blit(body_surf, body_surf.get_rect(centerx=box_rect.centerx, y=box_y + 65 + i * line_height))

        # Continue button
        btn_w, btn_h = 140, 40
        self._btn_rect = pygame.Rect(
            box_rect.centerx - btn_w // 2,
            box_y + box_h - btn_h - 20,
            btn_w, btn_h
        )
        pygame.draw.rect(screen, theme["btn"], self._btn_rect, border_radius=6)
        pygame.draw.rect(screen, theme["btn_border"], self._btn_rect, 2, border_radius=6)
        btn_surf = self.smallfont.render("Continue  [Enter]", True, (255, 255, 255))
        screen.blit(btn_surf, btn_surf.get_rect(center=self._btn_rect.center))
        

class InlineInput:
    """A field for a form row."""
    def __init__(self, x, y, w, h, font, placeholder="", is_float=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.is_float = is_float

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif self.is_float:
                if event.unicode.isdigit() or (event.unicode == "." and "." not in self.text):
                    if len(self.text) < 5: self.text += event.unicode
            else:
                if len(self.text) < 15: self.text += event.unicode

    def draw(self, screen):
        color = (70, 70, 100) if self.active else (40, 40, 60)
        border = (200, 200, 255) if self.active else (100, 100, 150)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=5)
        
        if not self.text:
            surf = self.font.render(self.placeholder, True, (90, 90, 120))
        else:
            surf = self.font.render(self.text, True, (255, 255, 255))
        
        screen.blit(surf, (self.rect.x + 5, self.rect.y + (self.rect.height - surf.get_height()) // 2))


class ScheduleSelector:
    """Explicit selection for Weekly/Biweekly."""
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.value = "weekly"
        self.weekly_rect = pygame.Rect(x, y, w // 2, h)
        self.biweekly_rect = pygame.Rect(x + w // 2, y, w // 2, h)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.weekly_rect.collidepoint(event.pos):
                self.value = "weekly"
            elif self.biweekly_rect.collidepoint(event.pos):
                self.value = "biweekly"

    def draw(self, screen):
        # Draw background and border
        pygame.draw.rect(screen, (40, 40, 60), self.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 150), self.rect, 2, border_radius=5)
        
        # Draw segments
        for val, rect, label in [("weekly", self.weekly_rect, "Weekly"), ("biweekly", self.biweekly_rect, "Biweekly")]:
            is_sel = self.value == val
            color = (52, 152, 219) if is_sel else (30, 30, 50)
            pygame.draw.rect(screen, color, rect, border_radius=5)
            if is_sel:
                pygame.draw.rect(screen, (200, 200, 255), rect, 2, border_radius=5)
            
            txt = self.font.render(label, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))


class SetupWizard:
    def __init__(self, font, smallfont, btn_font):
        self.font = font
        self.smallfont = smallfont
        self.btn_font = btn_font
        self.active = False
        self.done = False
        self.step = 0 # 0: Student Type, 1: num_theory, 2: theory_form, 3: num_labs, 4: lab_form
        
        self.result = {"student_type": "Average", "courses": [], "labs": []}

        # Step 0 Buttons
        bw, bh = 150, 45
        self.type_btns = [
            Button(0, 0, bw, bh, "Good", btn_font),
            Button(0, 0, bw, bh, "Average", btn_font),
            Button(0, 0, bw, bh, "Bad", btn_font)
        ]
        
        # Quantity screens
        self.qty_input = NumberBox(font, smallfont)
        self.qty_btn = Button(0, 0, 140, 40, "Next", btn_font)

        # Form tracking
        self.rows = []
        self.focus_idx = 0 # index in flat list of all InlineInputs
        self.form_btn = Button(0, 0, 180, 45, "Confirm Details", btn_font)
        self._error = ""

    def reset(self):
        self.active = True
        self.done = False
        self.step = 0
        self.result = {"student_type": "Average", "courses": [], "labs": []}
        self._error = ""

    def _build_form(self, count, type="Theory"):
        self.rows = []
        self._error = ""
        self.focus_idx = 0
        start_y = 180
        row_h = 50
        
        if type == "Theory":
            for i in range(count):
                name = InlineInput(250, start_y + i*row_h, 250, 35, self.smallfont, "Course Name")
                cred = InlineInput(520, start_y + i*row_h, 80, 35, self.smallfont, "Credits", is_float=True)
                self.rows.append({"name": name, "credits": cred})
        else: # Lab
            for i in range(count):
                name = InlineInput(150, start_y + i*row_h, 220, 35, self.smallfont, "Lab Name")
                # Explicit selector for schedule
                sched = ScheduleSelector(380, start_y + i*row_h, 180, 35, self.smallfont)
                cred = InlineInput(570, start_y + i*row_h, 80, 35, self.smallfont, "Credits", is_float=True)
                self.rows.append({"name": name, "sched": sched, "credits": cred})
        
        self._sync_focus()

    def _sync_focus(self):
        # Flatten only text-input fields for Tab navigation
        self.all_fields = []
        for r in self.rows:
            if "name" in r: self.all_fields.append(r["name"])
            if "credits" in r: self.all_fields.append(r["credits"])
        
        if self.all_fields:
            for i, f in enumerate(self.all_fields):
                f.active = (i == self.focus_idx)

    def handle_event(self, event):
        if not self.active: return

        if self.step == 0:
            for i, btn in enumerate(self.type_btns):
                if btn.clicked(event):
                    self.result["student_type"] = ["Good", "Average", "Bad"][i]
                    self.step = 1
                    self.qty_input.open("How many theory courses?", max_value=8)

        elif self.step == 1: # Qty Theory
            res = self.qty_input.handle_event(event)
            if res:
                self._build_form(res, "Theory")
                self.step = 2

        elif self.step == 2: # Theory Form
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    direction = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                    self.focus_idx = (self.focus_idx + direction) % len(self.all_fields)
                    self._sync_focus()
                    return
                if event.key == pygame.K_RETURN and not any(f.active for f in self.all_fields):
                    self._validate_theory()
                    return

            for f in self.all_fields:
                f.handle_event(event)
                if f.active: self.focus_idx = self.all_fields.index(f)

            if self.form_btn.clicked(event):
                self._validate_theory()

        elif self.step == 3: # Qty Lab
            res = self.qty_input.handle_event(event)
            if res is not None:
                if res == 0:
                    self.active = False
                    self.done = True
                else:
                    self._build_form(res, "Lab")
                    self.step = 4

        elif self.step == 4: # Lab Form
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    direction = -1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                    self.focus_idx = (self.focus_idx + direction) % len(self.all_fields)
                    self._sync_focus()
                    return

            # Handle ScheduleSelector events separately
            for r in self.rows:
                r["sched"].handle_event(event)

            # Handle text input fields
            for f in self.all_fields:
                f.handle_event(event)
                if f.active: self.focus_idx = self.all_fields.index(f)

            if self.form_btn.clicked(event):
                self._validate_labs()

    def _validate_theory(self):
        res = []
        for r in self.rows:
            if not r["name"].text or not r["credits"].text:
                self._error = "All fields are required!"
                return
            try:
                res.append({"name": r["name"].text, "credits": float(r["credits"].text)})
            except:
                self._error = "Invalid credit value!"
                return
        self.result["courses"] = res
        self.step = 3
        self.qty_input.open("How many labs?", max_value=6)

    def _validate_labs(self):
        res = []
        for r in self.rows:
            if not r["name"].text or not r["credits"].text:
                self._error = "All fields required!"
                return
            try:
                res.append({
                    "name": r["name"].text, 
                    "credits": float(r["credits"].text),
                    "schedule": r["sched"].value
                })
            except:
                self._error = "Invalid credit value!"
                return
        self.result["labs"] = res
        self.active = False
        self.done = True

    def draw(self, screen):
        if not self.active: return
        screen.fill((20, 20, 30))
        title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 40)
        
        def draw_centered(text, y, font=self.font, color=(255,255,255)):
            surf = font.render(text, True, color)
            screen.blit(surf, (screen.get_width()//2 - surf.get_width()//2, y))

        if self.step == 0:
            draw_centered("Welcome! What type of student are you?", 120, title_font)
            spacing = 200
            start_x = (screen.get_width() - (3 * 150 + 2 * spacing)) // 2
            for i, btn in enumerate(self.type_btns):
                btn.rect.x = start_x + i * (150 + spacing)
                btn.rect.y = 300
                btn.draw(screen)

        elif self.step == 1 or self.step == 3:
            draw_centered("Almost there...", 150, title_font)
            self.qty_input.draw(screen)

        elif self.step == 2:
            draw_centered("Enter Theory Course Details", 50, title_font)
            draw_centered("Tab to switch fields", 100, self.smallfont, (150, 150, 200))
            
            # Form Headers
            h_y = 145
            screen.blit(self.smallfont.render("Course Name", True, (200, 200, 255)), (250, h_y))
            screen.blit(self.smallfont.render("Credits", True, (200, 200, 255)), (520, h_y))

            for r in self.rows:
                r["name"].draw(screen)
                r["credits"].draw(screen)
            
            self.form_btn.rect.centerx = screen.get_width() // 2
            self.form_btn.rect.y = screen.get_height() - 100
            self.form_btn.draw(screen)
            if self._error: draw_centered(self._error, screen.get_height() - 140, self.smallfont, (255, 100, 100))

        elif self.step == 4:
            draw_centered("Enter Lab Details", 50, title_font)
            draw_centered("Click schedule to toggle (Weekly/Biweekly)", 100, self.smallfont, (150, 150, 200))
            
            h_y = 145
            screen.blit(self.smallfont.render("Lab Name", True, (200, 200, 255)), (150, h_y))
            screen.blit(self.smallfont.render("Schedule", True, (200, 200, 255)), (380, h_y))
            screen.blit(self.smallfont.render("Credits", True, (200, 200, 255)), (570, h_y))

            for r in self.rows:
                r["name"].draw(screen)
                r["sched"].draw(screen)
                r["credits"].draw(screen)
            
            self.form_btn.rect.centerx = screen.get_width() // 2
            self.form_btn.rect.y = screen.get_height() - 100
            self.form_btn.draw(screen)
            if self._error: draw_centered(self._error, screen.get_height() - 140, self.smallfont, (255, 100, 100))
