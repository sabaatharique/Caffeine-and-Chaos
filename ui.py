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


class Checkbox:
    _CB_ON  = (80, 200, 120)
    _CB_OFF = (80, 80, 110)

    def __init__(self, x, y, label: str, font, checked=False):
        self.rect = pygame.Rect(x, y, 22, 22)
        self.label = label
        self.font = font
        self.checked = checked

    def handle_event(self, event) -> bool:
        """Toggle on click; return new checked state."""
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.checked = not self.checked
        return self.checked

    def draw(self, screen):
        cb_col = self._CB_ON if self.checked else self._CB_OFF
        pygame.draw.rect(screen, cb_col, self.rect, border_radius=4)
        pygame.draw.rect(screen, (200, 210, 255), self.rect, 2, border_radius=4)
        if self.checked:
            cx, cy = self.rect.centerx, self.rect.centery
            pygame.draw.line(screen, (255, 255, 255),
                             (cx - 6, cy), (cx - 1, cy + 5), 3)
            pygame.draw.line(screen, (255, 255, 255),
                             (cx - 1, cy + 5), (cx + 7, cy - 5), 3)
        surf = self.font.render(self.label, True, (220, 220, 220))
        screen.blit(surf, (self.rect.right + 10, self.rect.y + (self.rect.height - surf.get_height()) // 2))


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
        self.color_type = "red"  # "red", "yellow", or "sickness"
        
        # Color themes
        self._themes = {
            "sickness": {
                "bg": (80, 20, 20),
                "border": (255, 30, 30),
                "title": (255, 100, 100),
                "btn": (200, 30, 30),
                "btn_border": (255, 150, 150),
                "overlay_tint": (100, 0, 0, 100)
            },
            "recovery": {
                "bg": (20, 60, 20),
                "border": (80, 255, 80),
                "title": (100, 255, 100),
                "btn": (40, 180, 40),
                "btn_border": (120, 255, 120),
                "overlay_tint": (0, 100, 0, 100)
            },
            "red": {
                "bg": (60, 20, 20),
                "border": (255, 80, 80),
                "title": (255, 80, 80),
                "btn": (180, 40, 40),
                "btn_border": (255, 120, 120),
                "overlay_tint": (0, 0, 0, 180)
            },
            "yellow": {
                "bg": (60, 60, 20),
                "border": (255, 220, 0),
                "title": (255, 220, 0),
                "btn": (180, 160, 40),
                "btn_border": (255, 230, 120),
                "overlay_tint": (0, 0, 0, 180)
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

        # Use theme-specific overlay tint
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill(theme["overlay_tint"])
        screen.blit(overlay, (0, 0))

        box_w, box_h = 540, 220 
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, theme["bg"], box_rect, border_radius=10)
        
        # Thicker border for sickness
        border_thickness = 4 if self.color_type == "sickness" else 2
        pygame.draw.rect(screen, theme["border"], box_rect, border_thickness, border_radius=10)

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
        


class ClassInterruptBox:
    """Modal interrupt shown when a scheduled class period begins.
    """

    _BG = (20, 28, 50)
    _BORDER = (100, 160, 255)
    _TITLE_C = (140, 200, 255)
    _BODY_C = (220, 225, 245)
    _ATTEND_C = (50, 200, 120)
    _SKIP_C = (200, 80,  80)
    _CB_ON = (80, 200, 120)
    _CB_OFF = (80, 80, 110)

    def __init__(self, font, smallfont):
        self.font = font
        self.smallfont = smallfont
        self.active = False
        self.attend_all = False  

        self._course = None
        self._start_hour = 0.0
        self._end_hour = 0.0
        self._attend_pct = 0.0
        self._result = None  # "attend" | "skip" | None

        # Rects computed in draw()
        self._attend_btn = None
        self._skip_btn = None
        self._cb_rect = None  

    def open(self, course, start_hour: float, end_hour: float, attendance_pct: float):
        self.active = True
        self._course = course
        self._start_hour = start_hour
        self._end_hour = end_hour
        self._attend_pct = attendance_pct
        self._result = None

    def handle_event(self, event) -> str | None:
        """Return "attend", "skip", or None."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_a:
                return self._confirm("attend")
            if event.key == pygame.K_s or event.key == pygame.K_ESCAPE:
                return self._confirm("skip")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Checkbox toggle
            if self._cb_rect and self._cb_rect.collidepoint(mx, my):
                self.attend_all = not self.attend_all
                return None

            # Attend button
            if self._attend_btn and self._attend_btn.collidepoint(mx, my):
                return self._confirm("attend")

            # Skip button
            if self._skip_btn and self._skip_btn.collidepoint(mx, my):
                return self._confirm("skip")

        return None

    def _confirm(self, result: str) -> str:
        self._result = result
        self.active  = False
        return result

    @staticmethod
    def _fmt(hour: float) -> str:
        """Convert fractional hour to 12-h string (reuses env logic inline)."""
        total_minutes = round(hour * 60)
        h = (total_minutes // 60) % 24
        m = total_minutes % 60
        if h == 0:
            return f"12:{m:02d} AM"
        elif h < 12:
            return f"{h}:{m:02d} AM"
        elif h == 12:
            return f"12:{m:02d} PM"
        else:
            return f"{h - 12}:{m:02d} PM"

    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_size()

        # Dim background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 500, 290
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, self._BG,    box_rect, border_radius=14)
        pygame.draw.rect(screen, self._BORDER, box_rect, 2, border_radius=14)

        # Bell icon stripe 
        stripe = pygame.Rect(box_x, box_y, box_w, 40)
        pygame.draw.rect(screen, (30, 50, 100), stripe,
                         border_radius=14)
        # Only round top corners (overdraw bottom corners)
        pygame.draw.rect(screen, (30, 50, 100),
                         pygame.Rect(box_x, box_y + 20, box_w, 20))

        bell_surf = self.font.render("Class Starting Now!", True, self._TITLE_C)
        screen.blit(bell_surf, bell_surf.get_rect(centerx=box_rect.centerx, y=box_y + 8))

        y = box_y + 58
        course_name = self._course.name if self._course else "Unknown"
        cname_surf = self.font.render(course_name, True, (255, 255, 255))
        screen.blit(cname_surf, cname_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += cname_surf.get_height() + 6

        time_str = f"{self._fmt(self._start_hour)} - {self._fmt(self._end_hour)}"
        time_surf = self.smallfont.render(time_str, True, self._BODY_C)
        screen.blit(time_surf, time_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += time_surf.get_height() + 4

        att_str = f"Attendance so far: {self._attend_pct:.0f}%"
        att_color = (231, 76, 60) if self._attend_pct < 75 else (46, 204, 113)
        att_surf = self.smallfont.render(att_str, True, att_color)
        screen.blit(att_surf, att_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += att_surf.get_height() + 18

        btn_w, btn_h = 160, 44
        gap = 20
        total_btn_w = btn_w * 2 + gap
        left_x = box_rect.centerx - total_btn_w // 2

        self._attend_btn = pygame.Rect(left_x, y, btn_w, btn_h)
        mouse = pygame.mouse.get_pos()
        attend_hov = self._attend_btn.collidepoint(mouse)
        attend_col = (40, 180, 100) if attend_hov else (30, 150, 80)
        pygame.draw.rect(screen, attend_col, self._attend_btn, border_radius=8)
        pygame.draw.rect(screen, self._ATTEND_C, self._attend_btn, 2, border_radius=8)
        a_surf = self.font.render("Attend  [A]", True, (255, 255, 255))
        screen.blit(a_surf, a_surf.get_rect(center=self._attend_btn.center))

        self._skip_btn = pygame.Rect(left_x + btn_w + gap, y, btn_w, btn_h)
        skip_hov = self._skip_btn.collidepoint(mouse)
        skip_col = (180, 50, 50) if skip_hov else (140, 30, 30)
        pygame.draw.rect(screen, skip_col, self._skip_btn, border_radius=8)
        pygame.draw.rect(screen, self._SKIP_C, self._skip_btn, 2, border_radius=8)
        s_surf = self.font.render("Skip  [S]", True, (255, 255, 255))
        screen.blit(s_surf, s_surf.get_rect(center=self._skip_btn.center))

        y += btn_h + 16

        cb_size = 22
        self._cb_rect = pygame.Rect(box_rect.centerx - 130, y + 2, cb_size, cb_size)
        cb_col = self._CB_ON if self.attend_all else self._CB_OFF
        pygame.draw.rect(screen, cb_col, self._cb_rect, border_radius=4)
        pygame.draw.rect(screen, (200, 210, 255), self._cb_rect, 2, border_radius=4)
        if self.attend_all:
            # Draw a checkmark tick
            cx, cy = self._cb_rect.centerx, self._cb_rect.centery
            pygame.draw.line(screen, (255, 255, 255),
                             (cx - 6, cy), (cx - 1, cy + 5), 3)
            pygame.draw.line(screen, (255, 255, 255),
                             (cx - 1, cy + 5), (cx + 7, cy - 5), 3)

        cb_label = self.smallfont.render("Attend all classes today", True, self._BODY_C)
        screen.blit(cb_label, (self._cb_rect.right + 10, y + (cb_size - cb_label.get_height()) // 2))


class QuizInterruptBox:
    """Modal shown during replay when a scheduled quiz slot is reached.
    Player can choose to Take or Skip the quiz regardless of replay mode.
    """

    _BG       = (20, 15, 45)
    _BORDER   = (200, 120, 255)
    _TITLE_C  = (220, 160, 255)
    _BODY_C   = (220, 215, 240)
    _TAKE_C   = (60, 200, 130)
    _SKIP_C   = (210, 70,  70)

    def __init__(self, font, smallfont):
        self.font      = font
        self.smallfont = smallfont
        self.active    = False

        self._course      = None
        self._quiz_number = 1
        self._take_btn    = None
        self._skip_btn    = None

    def open(self, course, quiz_number: int):
        self.active       = True
        self._course      = course
        self._quiz_number = quiz_number

    def handle_event(self, event) -> str | None:
        """Return 'take', 'skip', or None."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_t):
                return self._confirm("take")
            if event.key in (pygame.K_s, pygame.K_ESCAPE):
                return self._confirm("skip")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._take_btn and self._take_btn.collidepoint(mx, my):
                return self._confirm("take")
            if self._skip_btn and self._skip_btn.collidepoint(mx, my):
                return self._confirm("skip")

        return None

    def _confirm(self, result: str) -> str:
        self.active = False
        return result

    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 480, 230
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, self._BG,    box_rect, border_radius=14)
        pygame.draw.rect(screen, self._BORDER, box_rect, 2, border_radius=14)

        # Header stripe
        stripe = pygame.Rect(box_x, box_y, box_w, 40)
        pygame.draw.rect(screen, (40, 20, 80), stripe, border_radius=14)
        pygame.draw.rect(screen, (40, 20, 80),
                         pygame.Rect(box_x, box_y + 20, box_w, 20))

        title_surf = self.font.render("Quiz Time!", True, self._TITLE_C)
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_y + 8))

        y = box_y + 56
        course_name = self._course.name if self._course else "Unknown"
        cname_surf = self.font.render(
            f"Quiz {self._quiz_number} - {course_name}", True, (255, 255, 255))
        screen.blit(cname_surf, cname_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += cname_surf.get_height() + 8

        sub_surf = self.smallfont.render(
            "Do you want to take this quiz or skip it?", True, self._BODY_C)
        screen.blit(sub_surf, sub_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += sub_surf.get_height() + 20

        btn_w, btn_h = 160, 44
        gap = 20
        total_btn_w = btn_w * 2 + gap
        left_x = box_rect.centerx - total_btn_w // 2

        mouse = pygame.mouse.get_pos()

        self._take_btn = pygame.Rect(left_x, y, btn_w, btn_h)
        take_hov = self._take_btn.collidepoint(mouse)
        take_col = (40, 180, 100) if take_hov else (30, 150, 80)
        pygame.draw.rect(screen, take_col, self._take_btn, border_radius=8)
        pygame.draw.rect(screen, self._TAKE_C, self._take_btn, 2, border_radius=8)
        t_surf = self.font.render("Take  [T]", True, (255, 255, 255))
        screen.blit(t_surf, t_surf.get_rect(center=self._take_btn.center))

        self._skip_btn = pygame.Rect(left_x + btn_w + gap, y, btn_w, btn_h)
        skip_hov = self._skip_btn.collidepoint(mouse)
        skip_col = (180, 50, 50) if skip_hov else (140, 30, 30)
        pygame.draw.rect(screen, skip_col, self._skip_btn, border_radius=8)
        pygame.draw.rect(screen, self._SKIP_C, self._skip_btn, 2, border_radius=8)
        s_surf = self.font.render("Skip  [S]", True, (255, 255, 255))
        screen.blit(s_surf, s_surf.get_rect(center=self._skip_btn.center))


class LabAssessmentInterruptBox:
    """Modal shown during live-play and replay when a scheduled lab mid/final slot is reached.
    Player can choose to Take or Skip the assessment.
    """

    _BG       = (15, 35, 35)
    _BORDER   = (60, 220, 180)
    _TITLE_MID   = (80, 230, 200)
    _TITLE_FINAL = (255, 200, 80)
    _BODY_C   = (210, 240, 235)
    _TAKE_C   = (60, 200, 130)
    _SKIP_C   = (210, 70,  70)

    def __init__(self, font, smallfont):
        self.font      = font
        self.smallfont = smallfont
        self.active    = False

        self._course          = None
        self._assessment_type = "lab_mid"   # "lab_mid" or "lab_final"
        self._take_btn        = None
        self._skip_btn        = None

    def open(self, course, assessment_type: str):
        self.active            = True
        self._course           = course
        self._assessment_type  = assessment_type

    def handle_event(self, event) -> str | None:
        """Return 'take', 'skip', or None."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_t):
                return self._confirm("take")
            if event.key in (pygame.K_s, pygame.K_ESCAPE):
                return self._confirm("skip")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._take_btn and self._take_btn.collidepoint(mx, my):
                return self._confirm("take")
            if self._skip_btn and self._skip_btn.collidepoint(mx, my):
                return self._confirm("skip")

        return None

    def _confirm(self, result: str) -> str:
        self.active = False
        return result

    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        box_w, box_h = 480, 240
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(screen, self._BG,    box_rect, border_radius=14)
        pygame.draw.rect(screen, self._BORDER, box_rect, 2, border_radius=14)

        # Header stripe — teal for mid, amber for final
        is_final  = self._assessment_type == "lab_final"
        stripe_col = (20, 70, 55) if not is_final else (70, 50, 10)
        stripe = pygame.Rect(box_x, box_y, box_w, 40)
        pygame.draw.rect(screen, stripe_col, stripe, border_radius=14)
        pygame.draw.rect(screen, stripe_col,
                         pygame.Rect(box_x, box_y + 20, box_w, 20))

        label     = "Lab Final Exam!" if is_final else "Lab Midterm!"
        title_col = self._TITLE_FINAL if is_final else self._TITLE_MID
        title_surf = self.font.render(label, True, title_col)
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_y + 8))

        y = box_y + 58
        course_name = self._course.name if self._course else "Unknown"
        cname_surf = self.font.render(course_name, True, (255, 255, 255))
        screen.blit(cname_surf, cname_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += cname_surf.get_height() + 8

        sub_text = ("This is your Lab Final - give it everything!" if is_final
                    else "Lab Midterm time - show your practical skills!")
        sub_surf = self.smallfont.render(sub_text, True, self._BODY_C)
        screen.blit(sub_surf, sub_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += sub_surf.get_height() + 8

        prompt_surf = self.smallfont.render(
            "Do you want to take this assessment or skip it?", True, self._BODY_C)
        screen.blit(prompt_surf, prompt_surf.get_rect(centerx=box_rect.centerx, y=y))
        y += prompt_surf.get_height() + 18

        btn_w, btn_h = 160, 44
        gap = 20
        total_btn_w = btn_w * 2 + gap
        left_x = box_rect.centerx - total_btn_w // 2

        mouse = pygame.mouse.get_pos()

        self._take_btn = pygame.Rect(left_x, y, btn_w, btn_h)
        take_hov = self._take_btn.collidepoint(mouse)
        take_col = (40, 180, 100) if take_hov else (30, 150, 80)
        pygame.draw.rect(screen, take_col, self._take_btn, border_radius=8)
        pygame.draw.rect(screen, self._TAKE_C, self._take_btn, 2, border_radius=8)
        t_surf = self.font.render("Take  [T]", True, (255, 255, 255))
        screen.blit(t_surf, t_surf.get_rect(center=self._take_btn.center))

        self._skip_btn = pygame.Rect(left_x + btn_w + gap, y, btn_w, btn_h)
        skip_hov = self._skip_btn.collidepoint(mouse)
        skip_col = (180, 50, 50) if skip_hov else (140, 30, 30)
        pygame.draw.rect(screen, skip_col, self._skip_btn, border_radius=8)
        pygame.draw.rect(screen, self._SKIP_C, self._skip_btn, 2, border_radius=8)
        s_surf = self.font.render("Skip  [S]", True, (255, 255, 255))
        screen.blit(s_surf, s_surf.get_rect(center=self._skip_btn.center))


# Schedule Builder

# University timetable constants
_DAYS   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_SLOTS  = [
    ("8:00",  "9:15"),
    ("9:15",  "10:30"),
    ("10:30", "11:45"),
    ("11:45", "1:00"),
    ("1:00",  "2:30"),   
    ("2:30",  "3:45"),
    ("3:45",  "5:00"),
]
_LUNCH_IDX = 4   
_CLASS_SLOTS = [i for i in range(len(_SLOTS)) if i != _LUNCH_IDX]  


class ScheduleBuilder:
    """Interactive Mon-Fri weekly timetable.
    Usage
    -----
    builder = ScheduleBuilder(font, smallfont, btn_font)
    builder.set_courses(all_courses)      # list of Course objects
    # call handle_event / draw each frame
    # when builder.confirmed → read builder.get_schedule()
    """

    _CELL_W = 100 # per time-slot column
    _CELL_H = 72 # per day row
    _HEADER_H = 32 # slot-label row height at top
    _DAY_LABEL_W = 88 # width of the day-name column on the left
    _SIDE_W = 155 # course panel width (right side)
    _PAD = 12

    # colour palette
    _COL_HEADER = (30, 35, 55)
    _COL_EMPTY = (22, 28, 48)
    _COL_LUNCH = (28, 40, 28)
    _COL_HOVER = (40, 55, 80)
    _COL_BORDER = (60, 70, 100)
    _COL_LUNCH_BORDER = (40, 100, 60)
    _COL_SEL_PANEL_BG = (18, 20, 38)
    _COL_TEXT = (220, 225, 245)
    _COL_LUNCH_TEXT = (80, 200, 120)

    # 10 distinct pastel colours for course assignment
    _COURSE_COLORS = [
        (82,  130, 200), (200, 100,  80), (100, 180, 120),
        (200, 160,  60), (150,  90, 200), ( 60, 180, 200),
        (200,  80, 150), (130, 200,  70), (190, 120,  60),
        ( 80, 160, 190),
    ]

    def __init__(self, font, smallfont, btn_font):
        self.font = font
        self.smallfont = smallfont
        self.btn_font = btn_font

        self.courses: list = []
        self.selected_course = None # Course currently "held"
        # grid[day_idx][slot_idx] = Course or None  (pre-sized so draw() is safe before set_courses())
        self.grid: list[list] = [[None] * len(_SLOTS) for _ in range(len(_DAYS))]
        self._color_map: dict = {} # course → rgb tuple
        self.confirmed = False
        self._hover_cell = None # (day, slot) under mouse

        self._confirm_btn = Button(0, 0, 180, 42, "Confirm Schedule", btn_font)
        self._clear_btn = Button(0, 0, 120, 42, "Clear Cell", btn_font)
        self._skip_btn = Button(0, 0, 120, 42, "Skip", btn_font)

        # computed layout (set in draw)
        self._grid_rect = None
        self._cell_rects: list[list] = [] # [day][slot] → Rect
        self._course_rects: list = [] # sidebar rects

    def set_courses(self, courses: list):
        self.courses = list(courses)
        self.grid = [[None] * len(_SLOTS) for _ in range(len(_DAYS))]
        self._color_map = {
            c: self._COURSE_COLORS[i % len(self._COURSE_COLORS)]
            for i, c in enumerate(self.courses)
        }
        self.selected_course = self.courses[0] if self.courses else None
        self.confirmed = False
        self._hover_cell = None

    def get_schedule(self) -> dict:
        """Return {(day_idx, slot_idx): Course} for all filled cells."""
        out = {}
        for d, day_row in enumerate(self.grid):
            for s, course in enumerate(day_row):
                if course is not None:
                    out[(d, s)] = course
        return out

    # events
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover_cell = self._cell_at(mx, my)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Sidebar course selection
            for i, rect in enumerate(self._course_rects):
                if rect.collidepoint(mx, my):
                    self.selected_course = self.courses[i]
                    return

            # Grid cell click
            cell = self._cell_at(mx, my)
            if cell:
                d, s = cell
                if s == _LUNCH_IDX:
                    return   # can't assign to lunch
                if self.selected_course is not None:
                    # toggle off if same course already there
                    if self.grid[d][s] == self.selected_course:
                        self.grid[d][s] = None
                    else:
                        self.grid[d][s] = self.selected_course
                return

            # Buttons
            if self._confirm_btn.clicked(event):
                self.confirmed = True
            if self._clear_btn.clicked(event):
                # clear all cells with the selected course
                if self.selected_course:
                    for day_row in self.grid:
                        for s in range(len(day_row)):
                            if day_row[s] == self.selected_course:
                                day_row[s] = None
            if self._skip_btn.clicked(event):
                self.confirmed = True

    # drawing
    def draw(self, screen):
        sw, sh = screen.get_size()
        screen.fill((14, 16, 30))

        n_days  = len(_DAYS)
        n_slots = len(_SLOTS)
        cw = self._CELL_W # slot column width
        ch = self._CELL_H # day row height
        hh = self._HEADER_H # slot-header row
        dlw = self._DAY_LABEL_W # day-name column
        pad = self._PAD
        sw_side = self._SIDE_W

        # Layout: [day-label col][slot columns …][pad][sidebar]
        grid_total_w = dlw + n_slots * cw
        total_w = grid_total_w + pad + sw_side
        origin_x = (sw - total_w) // 2 # left edge of day-label column
        origin_y = 100 # top edge of slot-header row

        grid_x = origin_x + dlw # left edge of first slot column
        grid_y = origin_y + hh # top edge of first day row
        side_x = origin_x + grid_total_w + pad # left edge of sidebar

        # Title
        tf = pygame.font.Font("assets/fonts/Papernotes.otf", 36)
        title = tf.render("Build Your Weekly Schedule", True, (200, 215, 255))
        screen.blit(title, (sw // 2 - title.get_width() // 2, 12))
        hint = self.smallfont.render(
            "Select a course on the right, then click a cell to assign it.  Click again to remove.",
            True, (130, 140, 170))
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, 52))

        # "Placing" indicator (below hint, above grid)
        if self.selected_course:
            col = self._color_map.get(self.selected_course, (80, 100, 140))
            ind_surf = self.smallfont.render(
                f"Placing: {self.selected_course.name}", True, col)
            screen.blit(ind_surf, (origin_x + dlw, origin_y - 20))

        # Slot-header row (columns across the top)
        self._cell_rects = [[None] * n_slots for _ in range(n_days)]
        for s, (t_start, _t_end) in enumerate(_SLOTS):
            hdr_rect = pygame.Rect(grid_x + s * cw, origin_y, cw, hh)
            pygame.draw.rect(screen, self._COL_HEADER, hdr_rect)
            pygame.draw.rect(screen, self._COL_BORDER, hdr_rect, 1)
            if s == _LUNCH_IDX:
                label = "Lunch"
                lcol = self._COL_LUNCH_TEXT
            else:
                label = t_start
                lcol = self._COL_TEXT
            ls = self.smallfont.render(label, True, lcol)
            screen.blit(ls, ls.get_rect(center=hdr_rect.center))

        # Day rows
        for d, day in enumerate(_DAYS):
            # Day-name label cell (left column)
            lbl_rect = pygame.Rect(origin_x, grid_y + d * ch, dlw - 2, ch)
            pygame.draw.rect(screen, self._COL_HEADER, lbl_rect)
            pygame.draw.rect(screen, self._COL_BORDER, lbl_rect, 1)
            day_surf = self.smallfont.render(day, True, self._COL_TEXT)
            screen.blit(day_surf, day_surf.get_rect(center=lbl_rect.center))

            # Slot cells
            for s in range(n_slots):
                cell_rect = pygame.Rect(grid_x + s * cw, grid_y + d * ch, cw, ch)
                self._cell_rects[d][s] = cell_rect

                course = self.grid[d][s]
                is_lunch = (s == _LUNCH_IDX)
                is_hover = (self._hover_cell == (d, s)) and not is_lunch

                if is_lunch:
                    bg, border = self._COL_LUNCH, self._COL_LUNCH_BORDER
                elif course:
                    c = self._color_map.get(course, (80, 100, 140))
                    bg = c
                    border = tuple(min(255, v + 60) for v in c)
                elif is_hover:
                    bg, border = self._COL_HOVER, (100, 130, 200)
                else:
                    bg, border = self._COL_EMPTY, self._COL_BORDER

                pygame.draw.rect(screen, bg, cell_rect)
                pygame.draw.rect(screen, border, cell_rect, 1)

                if is_lunch and d == n_days // 2:
                    ls = self.smallfont.render("Break", True, self._COL_LUNCH_TEXT)
                    screen.blit(ls, ls.get_rect(center=cell_rect.center))
                elif course:
                    words = course.name.split()
                    lines, line = [], ""
                    for w in words:
                        test = (line + " " + w).strip()
                        if self.smallfont.size(test)[0] < cw - 8:
                            line = test
                        else:
                            lines.append(line)
                            line = w
                    if line:
                        lines.append(line)
                    total_th = len(lines) * (self.smallfont.get_height() + 2)
                    ty = cell_rect.y + (ch - total_th) // 2
                    for ln in lines:
                        ls = self.smallfont.render(ln, True, (255, 255, 255))
                        screen.blit(ls, (cell_rect.x + (cw - ls.get_width()) // 2, ty))
                        ty += self.smallfont.get_height() + 2

        # Grid outer border
        outer = pygame.Rect(grid_x, origin_y, n_slots * cw, hh + n_days * ch)
        pygame.draw.rect(screen, (80, 90, 130), outer, 2, border_radius=3)

        # Right sidebar: course list
        self._course_rects = []
        panel_bg = pygame.Rect(side_x - 4, origin_y - 4,
                               sw_side + 8, hh + n_days * ch + 8)
        pygame.draw.rect(screen, self._COL_SEL_PANEL_BG, panel_bg, border_radius=8)
        pygame.draw.rect(screen, (50, 60, 90), panel_bg, 1, border_radius=8)
        hdr_lbl = self.smallfont.render("Courses", True, (160, 170, 210))
        screen.blit(hdr_lbl,
                    (side_x + sw_side // 2 - hdr_lbl.get_width() // 2, origin_y))
        item_h = 36
        for i, c in enumerate(self.courses):
            r = pygame.Rect(side_x, origin_y + hh + 4 + i * (item_h + 6),
                            sw_side, item_h)
            self._course_rects.append(r)
            is_sel = (c == self.selected_course)
            col = self._color_map.get(c, (80, 100, 140))
            bg  = tuple(min(255, v + 40) for v in col) if is_sel \
                  else tuple(max(0, v - 20) for v in col)
            pygame.draw.rect(screen, bg, r, border_radius=7)
            brd = (255, 255, 255) if is_sel else col
            pygame.draw.rect(screen, brd, r, 2 if is_sel else 1, border_radius=7)
            ns = self.smallfont.render(c.name[:20], True, (255, 255, 255))
            screen.blit(ns, (r.x + 8, r.y + (r.height - ns.get_height()) // 2))

        # Buttons
        btn_y = grid_y + n_days * ch + 18
        self._confirm_btn.rect.centerx = sw // 2 + 80
        self._confirm_btn.rect.y = btn_y
        self._clear_btn.rect.centerx = sw // 2 - 80
        self._clear_btn.rect.y = btn_y
        self._skip_btn.rect.centerx = sw // 2 + 260
        self._skip_btn.rect.y = btn_y
        self._confirm_btn.draw(screen)
        self._clear_btn.draw(screen)
        self._skip_btn.draw(screen)

    # internals 
    def _cell_at(self, mx, my):
        for d, day_col in enumerate(self._cell_rects):
            for s, rect in enumerate(day_col):
                if rect and rect.collidepoint(mx, my):
                    return (d, s)
        return None


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


class Slider:
    """Horizontal slider for picking a float value in [min_val, max_val]."""

    def __init__(self, x, y, w, h, font, min_val=0.6, max_val=1.4, default=1.0,
                 labels=None):
        self.track_rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.min_val = min_val
        self.max_val = max_val
        self.value = default
        self.labels = labels or []
        self._dragging = False
        self.knob_r = h + 4
        self._update_knob()

    def _update_knob(self):
        frac = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_x = int(self.track_rect.x + frac * self.track_rect.w)
        self.knob_y = self.track_rect.centery

    def _set_from_x(self, x):
        frac = (x - self.track_rect.x) / self.track_rect.w
        frac = max(0.0, min(1.0, frac))
        self.value = self.min_val + frac * (self.max_val - self.min_val)
        self._update_knob()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            kx, ky = self.knob_x, self.knob_y
            mx, my = event.pos
            if (mx - kx) ** 2 + (my - ky) ** 2 <= self.knob_r ** 2:
                self._dragging = True
            elif self.track_rect.collidepoint(mx, my):
                self._set_from_x(mx)
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_from_x(event.pos[0])

    def draw(self, screen):
        tx, ty = self.track_rect.x, self.track_rect.y
        tw, th = self.track_rect.w, self.track_rect.h
        frac = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_w = int(tw * frac)

        # Track background
        pygame.draw.rect(screen, (50, 50, 70), self.track_rect, border_radius=th // 2)

        # Filled portion (red→green gradient by fraction)
        if fill_w > 0:
            r = int(220 * (1 - frac))
            g = int(180 * frac)
            fill_color = (r + 35, g + 60, 60)
            fill_rect = pygame.Rect(tx, ty, fill_w, th)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=th // 2)

        pygame.draw.rect(screen, (140, 140, 200), self.track_rect, 2, border_radius=th // 2)

        # Tick marks
        for val, text in self.labels:
            frac_t = (val - self.min_val) / (self.max_val - self.min_val)
            tick_x = int(tx + frac_t * tw)
            pygame.draw.line(screen, (200, 200, 255),
                             (tick_x, ty - 8), (tick_x, ty + th + 8), 2)
            lbl = self.font.render(text, True, (200, 200, 255))
            screen.blit(lbl, (tick_x - lbl.get_width() // 2, ty + th + 14))

        # Knob
        pygame.draw.circle(screen, (52, 200, 219), (self.knob_x, self.knob_y), self.knob_r)
        pygame.draw.circle(screen, (255, 255, 255), (self.knob_x, self.knob_y), self.knob_r, 2)

        # Value label removed


class SetupWizard:
    def __init__(self, font, smallfont, btn_font):
        self.font = font
        self.smallfont = smallfont
        self.btn_font = btn_font
        self.active = False
        self.done = False
        self.step = 0 # 0: Student Type, 1: num_theory, 2: theory_form, 3: num_labs, 4: lab_form, 5: schedule, 6: cgpa
        
        self.result = {"type_mult": 1.0, "target_cgpa": 0.0, "courses": [], "labs": [], "schedule": {}}

        # Step 0 Slider
        labels = [(0.6, "Bad"), (1.0, "Average"), (1.4, "Good")]
        self.type_slider = Slider(300, 300, 400, 15, font, min_val=0.6, max_val=1.4, labels=labels)
        self.type_confirm_btn = Button(425, 420, 150, 45, "Confirm", btn_font)

        # Step 6 Slider
        cgpa_labels = [(2.0, "2.0 (D)"), (3.0, "3.0 (B)"), (4.0, "4.0 (A+)")]
        self.cgpa_slider = Slider(300, 300, 400, 15, font, min_val=2.0, max_val=4.0, default=3.5, labels=cgpa_labels)
        self.cgpa_confirm_btn = Button(425, 420, 150, 45, "Confirm Target", btn_font)

        # Quantity screens
        self.qty_input = NumberBox(font, smallfont)
        self.qty_btn = Button(0, 0, 140, 40, "Next", btn_font)

        # Form tracking
        self.rows = []
        self.focus_idx = 0 # index in flat list of all InlineInputs
        self.form_btn = Button(0, 0, 180, 45, "Confirm Details", btn_font)
        self._error = ""

        # Step 5 – Schedule Builder
        self.schedule_builder = ScheduleBuilder(font, smallfont, btn_font)

    def reset(self):
        self.active = True
        self.done = False
        self.step = 0
        self.result = {"type_mult": 1.0, "target_cgpa": 0.0, "courses": [], "labs": [], "schedule": {}}
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
                cred.text = "1.0"   # default for weekly; auto-updates on schedule toggle
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
            self.type_slider.handle_event(event)
            if self.type_confirm_btn.clicked(event):
                self.result["type_mult"] = self.type_slider.value
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
                    self.step = 5  # skip lab form, go straight to schedule builder
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

            # Handle ScheduleSelector events separately; auto-fill default credits on toggle
            _DEFAULT_CREDITS = {"weekly": "1.0", "biweekly": "0.75"}
            _KNOWN_DEFAULTS = set(_DEFAULT_CREDITS.values()) | {"", "1", "0"}
            for r in self.rows:
                _old_sched = r["sched"].value
                r["sched"].handle_event(event)
                _new_sched = r["sched"].value
                if _old_sched != _new_sched and r["credits"].text in _KNOWN_DEFAULTS:
                    r["credits"].text = _DEFAULT_CREDITS[_new_sched]

            # Handle text input fields
            for f in self.all_fields:
                f.handle_event(event)
                if f.active: self.focus_idx = self.all_fields.index(f)

            if self.form_btn.clicked(event):
                self._validate_labs()

        elif self.step == 5:  # Schedule Builder
            self.schedule_builder.handle_event(event)
            if self.schedule_builder.confirmed:
                self.result["schedule"] = self.schedule_builder.get_schedule()
                self.step = 6

        elif self.step == 6:  # Target CGPA
            self.cgpa_slider.handle_event(event)
            if self.cgpa_confirm_btn.clicked(event):
                # Round to nearest 0.25
                val = round(self.cgpa_slider.value * 4) / 4
                self.result["target_cgpa"] = val
                self.active = False
                self.done = True

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
        # Move to schedule builder (step 5)
        self.step = 5
        # Provide the builder with all courses + labs combined
        all_courses = []  # will be populated by CourseManager after wizard;
        # pass empty – main will call schedule_builder.set_courses() after setup
        self.active = True  # stay active for step 5

    def draw(self, screen):
        if not self.active: return
        screen.fill((20, 20, 30))
        title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 40)
        
        def draw_centered(text, y, font=self.font, color=(255,255,255)):
            surf = font.render(text, True, color)
            screen.blit(surf, (screen.get_width()//2 - surf.get_width()//2, y))

        if self.step == 0:
            draw_centered("Welcome! Adjust your student potential:", 120, title_font)
            # Center the slider and button
            sw = screen.get_width()
            self.type_slider.track_rect.x = sw // 2 - self.type_slider.track_rect.w // 2
            self.type_slider.track_rect.y = 320
            self.type_slider._update_knob()
            self.type_slider.draw(screen)

            self.type_confirm_btn.rect.x = sw // 2 - self.type_confirm_btn.rect.w // 2
            self.type_confirm_btn.rect.y = 450
            self.type_confirm_btn.draw(screen)
            
            # help_text = "Bad (0.7) means slower progress, Good (1.4) means faster."
            # draw_centered(help_text, 200, self.smallfont, (180, 180, 220))

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

        elif self.step == 5:  # Schedule Builder
            self.schedule_builder.draw(screen)

        elif self.step == 6:
            draw_centered("What is your Target CGPA?", 120, title_font)
            sw = screen.get_width()
            self.cgpa_slider.track_rect.x = sw // 2 - self.cgpa_slider.track_rect.w // 2
            self.cgpa_slider.track_rect.y = 320
            self.cgpa_slider._update_knob()
            self.cgpa_slider.draw(screen)

            # Draw current value above the slider
            val = round(self.cgpa_slider.value * 4) / 4
            draw_centered(f"Target: {val:.2f}", 260, self.font, (255, 230, 150))

            self.cgpa_confirm_btn.rect.x = sw // 2 - self.cgpa_confirm_btn.rect.w // 2
            self.cgpa_confirm_btn.rect.y = 450
            self.cgpa_confirm_btn.draw(screen)

class QuizResultBox:
    """
    Shown immediately when a scheduled quiz fires.
    Displays course name, the auto-generated mark, and a grade band label.
    The player dismisses it with Enter or by clicking the card.
    """

    # Theme colours (match existing ui.py palette) 
    _CARD_BG      = (30, 30, 50, 230)
    _BORDER       = (120, 100, 200)
    _TEXT_WHITE   = (236, 240, 241)
    _TEXT_SUBTEXT = (180, 180, 220)
    _GRADE_COLORS = {          # keyed by letter grade
        "A":  (100, 255, 140),
        "B":  (120, 210, 255),
        "C":  (255, 220, 80),
        "D":  (255, 150, 60),
        "F":  (231, 76, 60),
    }

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.active    = False
        self._course   = None
        self._mark     = 0.0
        self._missed   = False  # True when the quiz fired but player was sick
        # Fonts are loaded lazily on first open (avoids pygame init order issues)
        self._title_font  = None
        self._body_font   = None
        self._hint_font   = None

    # public API 

    def open(self, course, missed: bool = False, quiz_number: int = 1, mark: float = 0.0):
        self._course = course
        self._missed = missed
        self._quiz_number = quiz_number
        self._mark = mark
        self.active  = True
        self._load_fonts()

    def close(self):
        self.active = False

    def handle_event(self, event) -> bool:
        """Return True if the box consumed the event."""
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                                           pygame.K_ESCAPE):
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.close()
            return True
        return False

    def draw(self, screen):
        if not self.active:
            return

        # dim the background 
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # card 
        card_w, card_h = 420, 200
        card_x = (self.screen_w - card_w) // 2
        card_y = (self.screen_h - card_h) // 2

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill(self._CARD_BG)
        screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(screen, (100, 100, 180), (card_x, card_y, card_w, card_h), 2, border_radius=10)

        # Title 
        title_text = f"Quiz {self._quiz_number} - {self._course.name}"
        title_surf = self._title_font.render(title_text, True, self._TEXT_WHITE)
        screen.blit(title_surf, (card_x + card_w // 2 - title_surf.get_width() // 2, card_y + 20))

        pygame.draw.line(screen, (80, 80, 140), (card_x + 40, card_y + 60), (card_x + card_w - 40, card_y + 60), 1)

        # Status 
        if self._missed:
            status_text = "Quiz Missed (sick or skipped)"
            status_color = (255, 100, 100)
            status_surf = self._body_font.render(status_text, True, status_color)
            screen.blit(status_surf, (card_x + card_w // 2 - status_surf.get_width() // 2, card_y + 90))

            note_text = f"Mark: {self._mark:.1f}/100"
            note_surf = self._hint_font.render(note_text, True, self._TEXT_SUBTEXT)
            screen.blit(note_surf, (card_x + card_w // 2 - note_surf.get_width() // 2, card_y + 125))
        else:
            status_text = f"Score: {self._mark:.1f}/100  ({self._grade_letter()})"
            status_color = self._grade_color()
            
            status_surf = self._body_font.render(status_text, True, status_color)
            screen.blit(status_surf, (card_x + card_w // 2 - status_surf.get_width() // 2, card_y + 90))

            note_text = self._band_label()
            note_surf = self._hint_font.render(note_text, True, self._TEXT_SUBTEXT)
            screen.blit(note_surf, (card_x + card_w // 2 - note_surf.get_width() // 2, card_y + 125))

        # dismiss hint 
        hint_surf = self._hint_font.render(
            "[ Enter to continue ]", True, (130, 130, 170))
        screen.blit(hint_surf,
                    (card_x + card_w // 2 - hint_surf.get_width() // 2,
                     card_y + card_h - 30))

    # private helpers 

    def _load_fonts(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 26)
            self._body_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
            self._hint_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 16)

    def _grade_letter(self) -> str:
        m = self._mark
        if m >= 80: return "A"
        if m >= 70: return "B"
        if m >= 60: return "C"
        if m >= 50: return "D"
        return "Referred"

    def _grade_color(self):
        return self._GRADE_COLORS[self._grade_letter()]

    def _band_label(self) -> str:
        m = self._mark
        if m >= 80: return "Excellent"
        if m >= 70: return "Good"
        if m >= 60: return "Average"
        if m >= 50: return "Passing"
        return "Failing"

class LabAssessmentResultBox(QuizResultBox):
    def open(self, course, missed: bool = False, assessment_type: str = "Lab Mid", mark: float = 0.0):
        self._course = course
        self._missed = missed
        self._assessment_type = assessment_type
        self._mark = mark
        self.active  = True
        self._load_fonts()

    def draw(self, screen):
        if not self.active:
            return

        # dim the background 
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # card 
        card_w, card_h = 420, 200
        card_x = (self.screen_w - card_w) // 2
        card_y = (self.screen_h - card_h) // 2

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill(self._CARD_BG)
        screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(screen, (100, 100, 180), (card_x, card_y, card_w, card_h), 2, border_radius=10)

        # Title 
        title_text = f"{self._assessment_type} - {self._course.name}"
        title_surf = self._title_font.render(title_text, True, self._TEXT_WHITE)
        screen.blit(title_surf, (card_x + card_w // 2 - title_surf.get_width() // 2, card_y + 20))

        pygame.draw.line(screen, (80, 80, 140), (card_x + 40, card_y + 60), (card_x + card_w - 40, card_y + 60), 1)

        # Status 
        if self._missed:
            status_text = "Assessment Missed (sick or skipped)"
            status_color = (255, 100, 100)
            status_surf = self._body_font.render(status_text, True, status_color)
            screen.blit(status_surf, (card_x + card_w // 2 - status_surf.get_width() // 2, card_y + 90))

            note_text = f"Mark: {self._mark:.1f}/100"
            note_surf = self._hint_font.render(note_text, True, self._TEXT_SUBTEXT)
            screen.blit(note_surf, (card_x + card_w // 2 - note_surf.get_width() // 2, card_y + 125))
        else:
            status_text = f"Score: {self._mark:.1f}/100  ({self._grade_letter()})"
            status_color = self._grade_color()
            
            status_surf = self._body_font.render(status_text, True, status_color)
            screen.blit(status_surf, (card_x + card_w // 2 - status_surf.get_width() // 2, card_y + 90))

            note_text = self._band_label()
            note_surf = self._hint_font.render(note_text, True, self._TEXT_SUBTEXT)
            screen.blit(note_surf, (card_x + card_w // 2 - note_surf.get_width() // 2, card_y + 125))

        # dismiss hint 
        hint_surf = self._hint_font.render(
            "[ Enter to continue ]", True, (130, 130, 170))
        screen.blit(hint_surf,
                    (card_x + card_w // 2 - hint_surf.get_width() // 2,
                     card_y + card_h - 30))

class QuizWeekPromptBox:
    """
    Shown at the start of a replayed week that contains one or more quizzes.
    Gives the player a choice:
        [Play Manually]   – stops the week-repeat loop and returns to GAME_SCREEN.
        [Keep Repeating]  – continues the normal fast-forward replay.

    Usage:
        box = QuizWeekPromptBox(font, small_font)
        box.open(next_week, quiz_list)      # quiz_list = [(day_name, time_str, course_name), ...]
        choice = box.handle_event(event)    # returns "manual" | "repeat" | None
        box.draw(screen)
    """

    _BG      = (18, 18, 40, 250)
    _BORDER  = (120, 90, 220)
    _TITLE   = (200, 180, 255)
    _BODY    = (210, 210, 235)
    _DIM     = (130, 125, 165)
    _BTN_MANUAL  = (50,  180, 230)    # teal – play manually
    _BTN_REPEAT  = (100, 80, 200)     # purple – keep repeating

    def __init__(self, font, small_font):
        self.font       = font
        self.small_font = small_font
        self.active     = False
        self._week      = 0
        self._quizzes   = []          # list of (day_str, time_str, course_name)
        self._manual_rect  = None
        self._repeat_rect  = None
        self._title_font   = None

    def open(self, week: int, quizzes: list):
        self.active   = True
        self._week    = week
        self._quizzes = quizzes

    def close(self):
        self.active = False

    def handle_event(self, event) -> str | None:
        """Return 'manual', 'repeat', or None."""
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:   # Space → play manually
                self.active = False
                return "manual"
            if event.key == pygame.K_r or event.key == pygame.K_RETURN:        # R or Enter → keep repeating
                self.active = False
                return "repeat"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._manual_rect and self._manual_rect.collidepoint(event.pos):
                self.active = False
                return "manual"
            if self._repeat_rect and self._repeat_rect.collidepoint(event.pos):
                self.active = False
                return "repeat"
        return None

    def draw(self, screen):
        if not self.active:
            return
        self._load_fonts()

        W, H = screen.get_width(), screen.get_height()

        # Dim overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Card geometry
        card_w = 500
        row_h  = 26
        n_rows = max(1, len(self._quizzes))
        card_h = 200 + n_rows * row_h
        card_x = (W - card_w) // 2
        card_y = (H - card_h) // 2

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill(self._BG)
        screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(screen, self._BORDER,
                         (card_x, card_y, card_w, card_h), 2, border_radius=12)

        # Title 
        title_surf = self._title_font.render(
            f"  Assessment Week Ahead!  ", True, self._TITLE)
        screen.blit(title_surf,
                    title_surf.get_rect(centerx=card_x + card_w // 2, y=card_y + 16))

        # Sub-heading 
        sub_surf = self.small_font.render(
            f"Week {self._week} has the following assessments scheduled:", True, self._BODY)
        screen.blit(sub_surf,
                    sub_surf.get_rect(centerx=card_x + card_w // 2, y=card_y + 54))

        # Quiz list 
        y = card_y + 82
        for q in self._quizzes:
            # q is a dict with {day, time, course_name, event_name}
            line = f"> {q['event_name']} : {q['course_name']}  ({q['day']} at {q['time']})"
            line_surf = self.small_font.render(line, True, (220, 200, 100))
            screen.blit(line_surf, line_surf.get_rect(centerx=card_x + card_w // 2, y=y))
            y += row_h

        # Separator 
        y += 10
        pygame.draw.line(screen, (60, 55, 100),
                         (card_x + 30, y), (card_x + card_w - 30, y), 1)
        y += 10

        # Hint 
        hint_surf = self.small_font.render(
            "How do you want to handle this week?", True, self._DIM)
        screen.blit(hint_surf,
                    hint_surf.get_rect(centerx=card_x + card_w // 2, y=y))
        y += 30

        # Buttons 
        btn_w, btn_h = 175, 42
        gap = 24
        total_btn_w = btn_w * 2 + gap
        btn_y = card_y + card_h - btn_h - 20

        # [Play Manually]
        self._manual_rect = pygame.Rect(
            card_x + card_w // 2 - total_btn_w // 2, btn_y, btn_w, btn_h)
        pygame.draw.rect(screen, self._BTN_MANUAL, self._manual_rect, border_radius=8)
        pygame.draw.rect(screen, (200, 240, 255), self._manual_rect, 2, border_radius=8)
        m_surf = self.small_font.render(" Play Manually ", True, (255, 255, 255))
        screen.blit(m_surf, m_surf.get_rect(center=self._manual_rect.center))

        # [Keep Repeating]
        self._repeat_rect = pygame.Rect(
            self._manual_rect.right + gap, btn_y, btn_w, btn_h)
        pygame.draw.rect(screen, self._BTN_REPEAT, self._repeat_rect, border_radius=8)
        pygame.draw.rect(screen, (200, 180, 255), self._repeat_rect, 2, border_radius=8)
        r_surf = self.small_font.render(" Keep Repeating ", True, (255, 255, 255))
        screen.blit(r_surf, r_surf.get_rect(center=self._repeat_rect.center))

    def _load_fonts(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 24)


class AcademicDashboard:

    # Dimensions 
    _PANEL_W       = 280   # expanded width
    _TAB_W         = 28    # collapsed tab width (visible strip on right edge)
    _PANEL_H_PAD   = 0     # top padding from screen top (full height)
    _ANIM_SPEED    = 8.0   # units/second — higher = faster slide

    # Colours 
    _C_BG          = (14, 14, 28, 240)   # deep navy, mostly opaque
    _C_TAB         = (26, 22, 52, 245)   # slightly lighter tab
    _C_EDGE        = (80, 60, 160)       # subtle purple edge line
    _C_GLOW        = (120, 90, 220)      # glow accent
    _C_SECTION_BG  = (24, 20, 46)        # section header background (solid)
    _C_TEXT        = (220, 215, 240)     # primary text
    _C_DIM         = (120, 115, 150)     # secondary / dim text
    _C_DIVIDER     = (40, 36, 72)        # divider line

    # Attendance
    _C_ATT_GOOD    = (50, 220, 120)     # ≥ 75 %
    _C_ATT_WARN    = (240, 190, 50)     # 50-74 %
    _C_ATT_BAD     = (220, 60, 60)      # < 50 %

    # Quiz urgency
    _C_QUIZ_THIS   = (235, 80, 80)      # this week — warm red
    _C_QUIZ_NEXT   = (240, 190, 50)     # next week — amber

    def __init__(self, screen_w: int, screen_h: int, font, small_font):
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.font       = font
        self.small_font = small_font

        self.expanded    = False          # start collapsed
        self._anim_t     = 0.0           # 0.0 = fully collapsed
        self._fonts_loaded = False
        self.scroll_y    = 0.0
        self.max_scroll  = 0.0
        self._collapse_arrow_rect = None  # set during draw; used by handle_event

        # Font handles (loaded lazily via _ensure_fonts)
        self._f_heading  = None   # section headers
        self._f_body     = None   # row text
        self._f_detail   = None   # secondary detail
        self._f_tab      = None   # collapsed tab label

    # public API 

    def update(self, dt: float):
        """Animate the slide.  Call every frame with dt in seconds."""
        target = 1.0 if self.expanded else 0.0
        diff   = target - self._anim_t
        if abs(diff) < 0.002:
            self._anim_t = target
        else:
            self._anim_t += diff * self._ANIM_SPEED * dt
            self._anim_t  = max(0.0, min(1.0, self._anim_t))

    def handle_event(self, event) -> bool:
        """Toggle on tab click when collapsed; collapse on outside click or arrow click when expanded."""
        if event.type == pygame.MOUSEWHEEL:
            if self.expanded:
                mx, my = pygame.mouse.get_pos()
                if mx >= self.screen_w - self._PANEL_W:
                    self.scroll_y -= event.y * 30
                    self.scroll_y = max(0.0, min(self.scroll_y, self.max_scroll))
                    return True
            return False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if not self.expanded:
                # Click on the collapsed tab strip -> expand
                if mx >= self.screen_w - self._TAB_W:
                    self.expanded = True
                    return True
                return False
            else:
                # Click on the collapse arrow -> collapse
                if (self._collapse_arrow_rect is not None
                        and self._collapse_arrow_rect.collidepoint(mx, my)):
                    self.expanded = False
                    self.scroll_y = 0.0
                    return True
                # Click outside expanded panel -> collapse
                if mx < self.screen_w - self._PANEL_W:
                    self.expanded = False
                    self.scroll_y = 0.0
                return True
        return False

    def draw(self, screen, course_manager, week_count: int):
        self._ensure_fonts()
        t = self._anim_t          # 0 = collapsed, 1 = expanded

        sw, sh = self.screen_w, self.screen_h
        panel_w = int(self._TAB_W + t * (self._PANEL_W - self._TAB_W))

        panel_x = sw - panel_w

        # Panel background 
        bg_surf = pygame.Surface((panel_w, sh), pygame.SRCALPHA)
        bg_surf.fill(self._C_BG)
        screen.blit(bg_surf, (panel_x, 0))

        # Soft left-edge glow line
        glow_alpha = int(180 + 75 * t)
        pygame.draw.line(screen, (*self._C_GLOW, glow_alpha),
                         (panel_x, 0), (panel_x, sh), 2)

        # ── Collapsed tab label: "Course Info" rotated vertically ──────────
        tab_label_alpha = int(max(0, (1.0 - t) / 0.5) * 220)
        if tab_label_alpha > 0 and self._f_tab is not None:
            tab_surf = self._f_tab.render("Course Info", True, (180, 155, 255))
            tab_rot  = pygame.transform.rotate(tab_surf, 90)
            tab_rect = tab_rot.get_rect(center=(sw - self._TAB_W // 2, sh // 2))
            tab_surf_alpha = pygame.Surface(tab_rot.get_size(), pygame.SRCALPHA)
            tab_surf_alpha.blit(tab_rot, (0, 0))
            tab_surf_alpha.set_alpha(tab_label_alpha)
            screen.blit(tab_surf_alpha, tab_rect)

        # ── Content (fades in as panel expands) 
        content_alpha = int(max(0, (t - 0.4) / 0.6) * 255)
        if content_alpha <= 0:
            return

        content_x = panel_x + self._TAB_W + 10
        content_w = panel_w - self._TAB_W - 20
        y         = 18 - int(self.scroll_y)

        old_clip = screen.get_clip()
        screen.set_clip((panel_x, 0, panel_w, sh))

        courses = course_manager.courses

        # ATTENDANCE  
        y = self._draw_section(screen, "ATTENDANCE", content_x, content_w, y,
                               content_alpha)

        if not courses:
            y = self._draw_dim_line(screen, "No courses enrolled.",
                                    content_x, y, content_alpha)
        else:
            for course in courses:
                tot_classes = max(1, course.total_classes)
                pct = min((course.attended_classes / tot_classes) * 100, 100.0)
                att_color = (
                    self._C_ATT_GOOD if pct >= 75 else
                    self._C_ATT_WARN if pct >= 50 else
                    self._C_ATT_BAD
                )

                # Course name
                name_surf = self._f_body.render(
                    self._truncate(course.name, 20), True,
                    self._alpha_color(self._C_TEXT, content_alpha))
                screen.blit(name_surf, (content_x, y))

                # Percentage and counts right-aligned
                count_text = f"{course.attended_classes}/{course.total_classes}"
                pct_text = f"({pct:.0f}%)"
                full_text = f"{count_text} {pct_text}"
                
                pct_surf = self._f_body.render(
                    full_text, True,
                    self._alpha_color(att_color, content_alpha))
                screen.blit(pct_surf,
                            (content_x + content_w - pct_surf.get_width(), y))

                y += name_surf.get_height() + 4

                # Progress bar (background)
                bar_h = 5
                bar_bg_surf = pygame.Surface((content_w, bar_h), pygame.SRCALPHA)
                bar_bg_surf.fill((40, 36, 72, content_alpha))
                screen.blit(bar_bg_surf, (content_x, y))

                # Progress fill with soft glow
                fill_w = int(content_w * min(pct, 100) / 100)
                if fill_w > 0:
                    fill_surf = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
                    fill_surf.fill((*att_color, content_alpha))
                    screen.blit(fill_surf, (content_x, y))

                    # Tiny glow cap at the right end of the bar
                    glow_cap = pygame.Surface((8, bar_h + 4), pygame.SRCALPHA)
                    cap_alpha = min(content_alpha, 180)
                    glow_cap.fill((*att_color, cap_alpha))
                    screen.blit(glow_cap, (content_x + fill_w - 4, y - 2))

                y += bar_h + 14

        # Divider
        y += 4
        divider_surf = pygame.Surface((content_w, 1), pygame.SRCALPHA)
        divider_surf.fill((*self._C_DIVIDER, content_alpha))
        screen.blit(divider_surf, (content_x, y))
        y += 12

        # UPCOMING QUIZZES  
        y = self._draw_section(screen, "UPCOMING QUIZZES", content_x, content_w, y,
                               content_alpha)

        # Collect only this week + next week
        upcoming = self._get_upcoming_quizzes(course_manager, week_count)

        if not upcoming:
            y = self._draw_dim_line(screen, "No quizzes soon.", content_x, y, content_alpha)
        else:
            from environment import SLOT_TIMES, DAYS_OF_WEEK, format_time
            for q in upcoming:
                weeks_away = q["week"] - week_count
                quiz_color = self._C_QUIZ_THIS if weeks_away == 0 else self._C_QUIZ_NEXT
                badge_text = "THIS WEEK" if weeks_away == 0 else "NEXT WEEK"
                
                day_short = DAYS_OF_WEEK[q["day_idx"]][:3]
                time_str  = format_time(SLOT_TIMES[q["slot_idx"]][0])

                # Row: Quiz N — Course
                label = f"Quiz {q['quiz_number']} : {self._truncate(q['course_name'], 18)}"
                subtitle = f"{day_short} @ {time_str} :  {badge_text}"
                y = self._draw_complex_line(screen, label, subtitle, content_x, y, content_alpha, quiz_color)

        # QUIZ HISTORY 
        y += 10
        y = self._draw_section(screen, "QUIZ HISTORY", content_x, content_w, y, content_alpha)
        
        history = self._get_quiz_history(course_manager)
        if not history:
            y = self._draw_dim_line(screen, "No attempts yet.", content_x, y, content_alpha)
        else:
            for q in history:
                mark = 0 if q["missed"] else q.get("mark", None)
                mark_str = f" ({mark:.0f}%)" if isinstance(mark, (int, float)) else " (N/A)"
                status = f"MISSED{mark_str}" if q["missed"] else f"TAKEN{mark_str}"
                st_color = (255, 120, 120) if q["missed"] else (120, 255, 180)
                
                line_text = f"Quiz {q['quiz_number']} : {self._truncate(q['course_name'], 15)}"
                y = self._draw_complex_line(screen, line_text, status, content_x, y, content_alpha, st_color)

        # UPCOMING LAB TESTS
        y += 10
        y = self._draw_section(screen, "UPCOMING LAB TESTS", content_x, content_w, y, content_alpha)
        
        upcoming_labs = self._get_upcoming_lab_assessments(course_manager, week_count)
        if not upcoming_labs:
            y = self._draw_dim_line(screen, "No lab tests soon.", content_x, y, content_alpha)
        else:
            from environment import SLOT_TIMES, DAYS_OF_WEEK, format_time
            for la in upcoming_labs:
                weeks_away = la["week"] - week_count
                lab_color = self._C_QUIZ_THIS if weeks_away == 0 else self._C_QUIZ_NEXT
                badge_text = "THIS WEEK" if weeks_away == 0 else "NEXT WEEK"
                
                day_short = DAYS_OF_WEEK[la["day_idx"]][:3]
                time_str  = format_time(SLOT_TIMES[la["slot_idx"]][0])
                atype = la["assessment_type"].replace('_', ' ').title()

                label = f"{atype} : {self._truncate(la['course_name'], 18)}"
                subtitle = f"{day_short} @ {time_str} :  {badge_text}"
                y = self._draw_complex_line(screen, label, subtitle, content_x, y, content_alpha, lab_color)

        # LAB TEST HISTORY 
        y += 10
        y = self._draw_section(screen, "LAB TEST HISTORY", content_x, content_w, y, content_alpha)
        
        lab_history = self._get_lab_history(course_manager)
        if not lab_history:
            y = self._draw_dim_line(screen, "No attempts yet.", content_x, y, content_alpha)
        else:
            for la in lab_history:
                mark = 0 if la["missed"] else la.get("mark", None)
                mark_str = f" ({mark:.0f}%)" if isinstance(mark, (int, float)) else " (N/A)"
                status = f"MISSED{mark_str}" if la["missed"] else f"TAKEN{mark_str}"
                st_color = (255, 120, 120) if la["missed"] else (120, 255, 180)
                
                atype = la["assessment_type"].replace('_', ' ').title()
                line_text = f"{atype} : {self._truncate(la['course_name'], 15)}"
                y = self._draw_complex_line(screen, line_text, status, content_x, y, content_alpha, st_color)

        screen.set_clip(old_clip)
        total_h = y + int(self.scroll_y)
        self.max_scroll = max(0.0, total_h - sh + 20)

        # ── Collapse arrow (inner left edge of expanded panel) ───────────────
        arrow_alpha = int(max(0, (t - 0.5) / 0.5) * 210)
        if arrow_alpha > 0:
            ar = 10  # radius
            ax = panel_x + ar + 2
            ay = sh // 2
            self._collapse_arrow_rect = pygame.Rect(ax - ar, ay - ar, ar * 2, ar * 2)
            # Circle background
            arrow_bg = pygame.Surface((ar * 2, ar * 2), pygame.SRCALPHA)
            pygame.draw.circle(arrow_bg, (60, 50, 110, arrow_alpha), (ar, ar), ar)
            pygame.draw.circle(arrow_bg, (*self._C_GLOW, arrow_alpha), (ar, ar), ar, 1)
            screen.blit(arrow_bg, (ax - ar, ay - ar))
            # "▶" chevron (points right → collapse into right wall)
            if self._f_tab is not None:
                ch_surf = self._f_tab.render(">", True, (200, 180, 255))
                ch_surf.set_alpha(arrow_alpha)
                screen.blit(ch_surf, ch_surf.get_rect(center=(ax, ay)))
        else:
            self._collapse_arrow_rect = None

    # private helpers 

    def _tab_rect(self) -> pygame.Rect:
        return pygame.Rect(self.screen_w - self._TAB_W, 0,
                           self._TAB_W, self.screen_h)

    def _ensure_fonts(self):
        if self._fonts_loaded:
            return
        self._f_heading = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._f_body    = pygame.font.Font("assets/fonts/Papernotes.otf", 17)
        self._f_detail  = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._f_tab     = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._fonts_loaded = True

    def _draw_section(self, screen, title: str,
                      x: int, w: int, y: int, alpha: int) -> int:
        """Draw a clean section label. Returns new y."""
        lbl_surf = self._f_heading.render(title, True,
                                           self._alpha_color(self._C_GLOW, alpha))
        screen.blit(lbl_surf, (x, y))
        y += lbl_surf.get_height() + 2
        # Thin underline
        line_surf = pygame.Surface((w, 1), pygame.SRCALPHA)
        line_surf.fill((*self._C_GLOW, alpha // 3))
        screen.blit(line_surf, (x, y))
        return y + 10

    def _draw_dim_line(self, screen, text: str, x: int, y: int, alpha: int) -> int:
        surf = self._f_detail.render(text, True,
                                      self._alpha_color(self._C_DIM, alpha))
        screen.blit(surf, (x, y))
        return y + surf.get_height() + 8

    @staticmethod
    def _alpha_color(rgb, alpha: int):
        """Clamp alpha and return a 3-tuple (SRCALPHA surfaces handle alpha separately)."""
        return (rgb[0], rgb[1], rgb[2])   # pygame.font.render uses solid colour; opacity is via Surface alpha

    @staticmethod
    def _truncate(s: str, max_chars: int) -> str:
        return s if len(s) <= max_chars else s[:max_chars - 1] + "…"

    def _draw_complex_line(self, screen, title: str, subtitle: str,
                           x: int, y: int, alpha: int, accent_color: tuple) -> int:
        """Draw a two-line row (Title / Subtitle) with an accent."""
        title_surf = self._f_body.render(title, True, self._alpha_color(self._C_TEXT, alpha))
        screen.blit(title_surf, (x, y))
        y += title_surf.get_height()
        
        sub_surf = self._f_detail.render(subtitle, True, self._alpha_color(accent_color, alpha))
        screen.blit(sub_surf, (x, y))
        return y + sub_surf.get_height() + 8

    def _get_upcoming_quizzes(self, course_manager, week_count: int) -> list[dict]:
        """Fetch quizzes for this week and next week."""
        res = []
        for course in course_manager.courses:
            if course.course_type != "Theory": continue
            for q in course.scheduled_quizzes:
                if q["taken"]: continue
                weeks_away = q["week"] - week_count
                if 0 <= weeks_away <= 1:
                    res.append({**q, "course_name": course.name})
        # Sort chronologically
        res.sort(key=lambda x: (x["week"], x["day_idx"], x["slot_idx"]))
        return res

    def _get_upcoming_lab_assessments(self, course_manager, week_count: int) -> list[dict]:
        """Fetch lab assessments for this week and next week."""
        res = []
        for course in course_manager.courses:
            if course.course_type != "Lab": continue
            for la in getattr(course, "scheduled_lab_assessments", []):
                if la["taken"]: continue
                weeks_away = la["week"] - week_count
                if 0 <= weeks_away <= 1:
                    res.append({**la, "course_name": course.name})
        res.sort(key=lambda x: (x["week"], x["day_idx"], x["slot_idx"]))
        return res

    def _get_quiz_history(self, course_manager) -> list[dict]:
        """Fetch all quizzes that have already been taken or missed."""
        res = []
        for course in course_manager.courses:
            if course.course_type != "Theory": continue
            for q in course.scheduled_quizzes:
                if q["taken"]:
                    res.append({**q, "course_name": course.name})
        # Sort by week (descending) then quiz number
        res.sort(key=lambda x: (x["week"], x["quiz_number"]), reverse=True)
        return res

    def _get_lab_history(self, course_manager) -> list[dict]:
        """Fetch all lab tests that have already been taken or missed."""
        res = []
        for course in course_manager.courses:
            if course.course_type != "Lab": continue
            for la in course.scheduled_lab_assessments:
                if la["taken"]:
                    res.append({**la, "course_name": course.name})
        # Sort by week (descending)
        res.sort(key=lambda x: x["week"], reverse=True)
        return res


class StatsDashboard:
    """Left-side sliding panel showing lifetime student statistics."""

    _PANEL_W     = 280
    _TAB_W       = 28    # visible tab strip when collapsed
    _ANIM_SPEED  = 8.0

    _C_BG        = (14, 14, 28, 240)
    _C_EDGE      = (80, 60, 160)
    _C_GLOW      = (120, 90, 220)
    _C_TEXT      = (220, 215, 240)
    _C_DIM       = (120, 115, 150)
    _C_DIVIDER   = (40, 36, 72)

    _C_TIME      = (80, 200, 240)
    _C_WELLNESS  = (240, 130, 60)
    _C_LIFESTYLE = (240, 210, 60)
    _C_RECORDS   = (190, 100, 240)
    _C_GOOD      = (50, 220, 120)
    _C_WARN      = (240, 190, 50)
    _C_BAD       = (220, 60, 60)

    def __init__(self, screen_w: int, screen_h: int, font, small_font):
        self.screen_w      = screen_w
        self.screen_h      = screen_h
        self.font          = font
        self.small_font    = small_font
        self.expanded      = False
        self._anim_t       = 0.0
        self._fonts_loaded = False
        self.scroll_y      = 0.0
        self.max_scroll    = 0.0
        self._collapse_arrow_rect = None  # set during draw; used by handle_event
        self._f_heading    = None
        self._f_body       = None
        self._f_detail     = None
        self._f_tab        = None

    def update(self, dt: float):
        """Animate the slide. Call every frame with dt in seconds."""
        target = 1.0 if self.expanded else 0.0
        diff   = target - self._anim_t
        if abs(diff) < 0.002:
            self._anim_t = target
        else:
            self._anim_t += diff * self._ANIM_SPEED * dt
            self._anim_t  = max(0.0, min(1.0, self._anim_t))

    def handle_event(self, event) -> bool:
        """Toggle on tab click when collapsed; collapse on outside click or arrow click when expanded."""
        if event.type == pygame.MOUSEWHEEL:
            if self.expanded:
                mx, my = pygame.mouse.get_pos()
                if mx <= self._PANEL_W:
                    self.scroll_y -= event.y * 30
                    self.scroll_y = max(0.0, min(self.scroll_y, self.max_scroll))
                    return True
            return False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if not self.expanded:
                # Click on the collapsed tab strip -> expand
                if mx <= self._TAB_W:
                    self.expanded = True
                    return True
                return False
            else:
                # Click on the collapse arrow -> collapse
                if (self._collapse_arrow_rect is not None
                        and self._collapse_arrow_rect.collidepoint(mx, my)):
                    self.expanded = False
                    self.scroll_y = 0.0
                    return True
                # Click outside expanded panel -> collapse
                if mx > self._PANEL_W:
                    self.expanded = False
                    self.scroll_y = 0.0
                return True

        return False

    def draw(self, screen, student, day_count: int, week_count: int = 0):
        self._ensure_fonts()
        t = self._anim_t

        sw, sh  = self.screen_w, self.screen_h
        panel_w = int(self._TAB_W + t * (self._PANEL_W - self._TAB_W))

        bg_surf = pygame.Surface((panel_w, sh), pygame.SRCALPHA)
        bg_surf.fill(self._C_BG)
        screen.blit(bg_surf, (0, 0))

        glow_alpha = int(180 + 75 * t)
        pygame.draw.line(screen,
                         (*self._C_GLOW, glow_alpha),
                         (panel_w, 0), (panel_w, sh), 2)

        # ── Collapsed tab label: "My Stats" rotated vertically ─────────────
        tab_label_alpha = int(max(0, (1.0 - t) / 0.5) * 220)
        if tab_label_alpha > 0 and self._f_tab is not None:
            tab_surf = self._f_tab.render("My Stats", True, (180, 155, 255))
            tab_rot  = pygame.transform.rotate(tab_surf, -90)
            tab_rect = tab_rot.get_rect(center=(self._TAB_W // 2, sh // 2))
            tab_surf_alpha = pygame.Surface(tab_rot.get_size(), pygame.SRCALPHA)
            tab_surf_alpha.blit(tab_rot, (0, 0))
            tab_surf_alpha.set_alpha(tab_label_alpha)
            screen.blit(tab_surf_alpha, tab_rect)

        content_alpha = int(max(0, (t - 0.4) / 0.6) * 255)
        if content_alpha <= 0:
            return

        content_x = self._TAB_W + 10
        content_w = panel_w - self._TAB_W - 20
        y         = 18 - int(self.scroll_y)

        old_clip = screen.get_clip()
        screen.set_clip((0, 0, panel_w, sh))

        y = self._draw_trends_section(screen, student, week_count,
                                       content_x, content_w, y, content_alpha)
        y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
        y = self._draw_time_section(screen, student, day_count,
                                    content_x, content_w, y, content_alpha)
        y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
        y = self._draw_academic_section(screen, student, day_count,
                                         content_x, content_w, y, content_alpha)
        y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
        y = self._draw_wellness_section(screen, student,
                                         content_x, content_w, y, content_alpha)
        y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
        y = self._draw_lifestyle_section(screen, student, day_count,
                                          content_x, content_w, y, content_alpha)
        y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
        y = self._draw_records_section(screen, student,
                                        content_x, content_w, y, content_alpha)

        screen.set_clip(old_clip)
        self.max_scroll = max(0.0, y + int(self.scroll_y) - sh + 20)

        # ── Collapse arrow (inner right edge of expanded panel) ──────────────
        arrow_alpha = int(max(0, (t - 0.5) / 0.5) * 210)
        if arrow_alpha > 0:
            ar = 10  # radius
            ax = panel_w - ar - 2
            ay = sh // 2
            self._collapse_arrow_rect = pygame.Rect(ax - ar, ay - ar, ar * 2, ar * 2)
            # Circle background
            arrow_bg = pygame.Surface((ar * 2, ar * 2), pygame.SRCALPHA)
            pygame.draw.circle(arrow_bg, (60, 50, 110, arrow_alpha), (ar, ar), ar)
            pygame.draw.circle(arrow_bg, (*self._C_GLOW, arrow_alpha), (ar, ar), ar, 1)
            screen.blit(arrow_bg, (ax - ar, ay - ar))
            # "◀" chevron (points left → collapse into left wall)
            if self._f_tab is not None:
                ch_surf = self._f_tab.render("<", True, (200, 180, 255))
                ch_surf.set_alpha(arrow_alpha)
                screen.blit(ch_surf, ch_surf.get_rect(center=(ax, ay)))
        else:
            self._collapse_arrow_rect = None

    # ── Section renderers ────────────────────────────────────────────────

    def _draw_trends_section(self, screen, student, week_count,
                             x: int, w: int, y: int, alpha: int) -> int:
        """Draw the TRENDS section: stat arrows, best day, and a mini stacked bar."""
        y = self._draw_section(screen, "THIS WEEK'S TRENDS", x, w, y, alpha)

        stress_snap = student._week_stress_snapshots
        health_snap = student._week_health_snapshots
        motiv_snap  = student._week_motivation_snapshots

        def _trend(snap: list, higher_is_better: bool):
            """Return (arrow_str, delta_str, color) for a snapshot list."""
            if len(snap) < 2:
                return "–", "n/a", self._C_DIM
            delta = snap[-1] - snap[0]
            if abs(delta) < 1.0:
                return "–", f"{delta:+.0f}", self._C_DIM
            if higher_is_better:
                arrow = "↑" if delta > 0 else "↓"
                color = self._C_GOOD if delta > 0 else self._C_BAD
            else:
                arrow = "↑" if delta > 0 else "↓"
                color = self._C_BAD if delta > 0 else self._C_GOOD
            return arrow, f"{delta:+.0f}", color

        # -- Stress / Health / Motivation trends --
        for label, snap, higher_good in [
            ("Stress",     stress_snap, False),
            ("Health",     health_snap, True),
            ("Motivation", motiv_snap,  True),
        ]:
            arrow, delta_str, color = _trend(snap, higher_good)
            lbl_surf = self._f_body.render(
                f"{label}", True, self._alpha_color(self._C_TEXT, alpha))
            val_surf = self._f_body.render(
                f"{arrow} {delta_str}", True, self._alpha_color(color, alpha))
            screen.blit(lbl_surf, (x, y))
            screen.blit(val_surf, (x + w - val_surf.get_width(), y))
            y += lbl_surf.get_height() + 5

        # -- Best day this week --
        y += 4
        best_day_surf = self._f_body.render(
            "Best Day", True, self._alpha_color(self._C_LIFESTYLE, alpha))
        screen.blit(best_day_surf, (x, y))

        study_h = student._week_study_hours
        best_label = "–"
        if study_h and stress_snap:
            from environment import DAYS_OF_WEEK
            scores = [
                study_h[i] * 2 - stress_snap[i]
                for i in range(min(len(study_h), len(stress_snap)))
            ]
            best_idx = scores.index(max(scores))
            best_label = DAYS_OF_WEEK[best_idx % 7][:3]  # e.g. "Mon"

        best_val_surf = self._f_body.render(
            best_label, True, self._alpha_color(self._C_GOOD, alpha))
        screen.blit(best_val_surf, (x + w - best_val_surf.get_width(), y))
        y += best_day_surf.get_height() + 8

        # -- Mini stacked bar chart (Study | Sleep | Relax | Class) --
        study_total = sum(student._week_study_hours)  if student._week_study_hours  else 0.0
        sleep_total = sum(student._week_sleep_hours)  if student._week_sleep_hours  else 0.0
        relax_total = sum(student._week_relax_hours)  if student._week_relax_hours  else 0.0
        class_total = sum(student._week_class_hours)  if student._week_class_hours  else 0.0
        grand_total = study_total + sleep_total + relax_total + class_total

        segments = [
            ("Study", study_total, self._C_TIME),
            ("Sleep", sleep_total, self._C_GOOD),
            ("Relax", relax_total, self._C_RECORDS),
            ("Class", class_total, self._C_WARN),
        ]

        bar_h = 14
        if grand_total > 0:
            bar_surf = pygame.Surface((w, bar_h), pygame.SRCALPHA)
            bar_surf.fill((*self._C_DIVIDER, alpha))
            cursor_x = 0
            for seg_label, seg_h, seg_color in segments:
                seg_w = int(w * seg_h / grand_total)
                if seg_w > 0:
                    pygame.draw.rect(bar_surf, (*seg_color, alpha),
                                     (cursor_x, 0, seg_w, bar_h))
                    cursor_x += seg_w
            screen.blit(bar_surf, (x, y))
        else:
            empty_surf = pygame.Surface((w, bar_h), pygame.SRCALPHA)
            empty_surf.fill((*self._C_DIVIDER, alpha))
            screen.blit(empty_surf, (x, y))
        y += bar_h + 3

        # Labels below the bar
        lbl_x = x
        lbl_y = y
        for seg_label, seg_h, seg_color in segments:
            seg_txt = f"{seg_label} {seg_h:.1f}h"
            seg_surf = self._f_detail.render(
                seg_txt, True, self._alpha_color(seg_color, alpha))
            # Wrap to next line if overflows
            if lbl_x + seg_surf.get_width() > x + w:
                lbl_x = x
                lbl_y += seg_surf.get_height() + 2
            screen.blit(seg_surf, (lbl_x, lbl_y))
            lbl_x += seg_surf.get_width() + 8
        y = lbl_y + self._f_detail.get_height() + 8

        return y

    def _draw_time_section(self, screen, student, day_count,
                           x, w, y, alpha) -> int:
        y    = self._draw_section(screen, "TIME BREAKDOWN", x, w, y, alpha)
        s    = student.stats
        days = max(1, day_count)
        rows = [
            ("Study",     s["hours_studied"],    self._C_TIME,      True),
            ("Sleep",     s["hours_slept"],       self._C_GOOD,      True),
            ("Relax",     s["hours_relaxed"],     self._C_RECORDS,   True),
            ("Class",     s["hours_in_class"],    self._C_WARN,      True),
            ("WiFi Lost", s["hours_wifi_outage"], self._C_BAD,       False),
        ]
        max_h = max((r[1] for r in rows), default=1.0) or 1.0
        for label, hours, color, show_avg in rows:
            lbl_surf = self._f_body.render(label, True,
                                            self._alpha_color(self._C_TEXT, alpha))
            screen.blit(lbl_surf, (x, y))
            val_surf = self._f_detail.render(f"{hours:.1f} h", True,
                                              self._alpha_color(color, alpha))
            screen.blit(val_surf, (x + w - val_surf.get_width(), y))
            y += lbl_surf.get_height() + 2
            y = self._draw_mini_bar(screen, x, w, y, hours / max_h, color, alpha)
            if show_avg:
                avg      = hours / days
                avg_surf = self._f_detail.render(f"avg {avg:.1f} h/day", True,
                                                  self._alpha_color(self._C_DIM, alpha))
                screen.blit(avg_surf, (x, y))
                y += avg_surf.get_height() + 8
            else:
                y += 8
        return y

    def _draw_academic_section(self, screen, student, day_count,
                                x, w, y, alpha) -> int:
        y        = self._draw_section(screen, "ACADEMIC RECORD", x, w, y, alpha)
        s        = student.stats
        attended = s["classes_attended"]
        skipped  = s["classes_skipped"]
        total    = max(1, attended + skipped)
        att_pct  = attended / total * 100
        att_color = (self._C_GOOD if att_pct >= 75 else
                     self._C_WARN if att_pct >= 50 else
                     self._C_BAD)
        rows = [
            ("Classes Attended", f"{attended}",
             self._C_GOOD),
            ("Classes Skipped",  f"{skipped}",
             self._C_BAD if skipped > 0 else self._C_DIM),
            ("Attendance Rate",  f"{att_pct:.0f}%",
             att_color),
            ("Target CGPA",      f"{student.target_cgpa:.2f}",
             self._C_RECORDS),
        ]
        for label, value, color in rows:
            y = self._draw_key_value(screen, label, value, x, w, y, alpha, color)
        return y

    def _draw_wellness_section(self, screen, student,
                                x, w, y, alpha) -> int:
        y = self._draw_section(screen, "WELLNESS RECORD", x, w, y, alpha)
        s = student.stats

        def _wcol(v):
            return self._C_WELLNESS if v > 0 else self._C_GOOD

        rows = [
            ("Times Sick",
             f"{s['times_sick']}",              _wcol(s['times_sick'])),
            ("Total Sick Days",
             f"{s['total_sick_days']}",          _wcol(s['total_sick_days'])),
            ("Longest Sick Streak",
             f"{s['longest_sick_streak']} days", _wcol(s['longest_sick_streak'])),
            ("Burnout Episodes",
             f"{s['burnout_occurrences']}",      _wcol(s['burnout_occurrences'])),
            ("Days Burnt Out",
             f"{s['days_burnt_out']}",           _wcol(s['days_burnt_out'])),
        ]
        for label, value, color in rows:
            y = self._draw_key_value(screen, label, value, x, w, y, alpha, color)

        if student.consecutive_stress_days >= 3:
            hint = f"! High stress {student.consecutive_stress_days} days in a row"
            hint_surf = self._f_detail.render(
                hint, True, self._alpha_color(self._C_BAD, alpha))
            screen.blit(hint_surf, (x, y))
            y += hint_surf.get_height() + 6
        return y

    def _draw_lifestyle_section(self, screen, student, day_count,
                                 x, w, y, alpha) -> int:
        y    = self._draw_section(screen, "LIFESTYLE", x, w, y, alpha)
        s    = student.stats
        days = max(1, day_count)
        coffees = s["coffees_drunk"]
        meals   = s["meals_eaten"]
        cpd     = coffees / days
        mpd     = meals   / days
        c_color = self._C_BAD if cpd > 2.0 else self._C_LIFESTYLE
        m_color = self._C_GOOD if mpd >= 2.0 else self._C_WARN
        y = self._draw_key_value(screen, "Coffees Drunk",
                                  f"{coffees}  ({cpd:.1f}/day)",
                                  x, w, y, alpha, c_color)
        y = self._draw_key_value(screen, "Meals Eaten",
                                  f"{meals}  ({mpd:.1f}/day)",
                                  x, w, y, alpha, m_color)
        if mpd < 1.5:
            warn_surf = self._f_detail.render(
                "Eat more! Low meals hurt health.", True,
                self._alpha_color(self._C_BAD, alpha))
            screen.blit(warn_surf, (x, y))
            y += warn_surf.get_height() + 6
        return y

    def _draw_records_section(self, screen, student,
                               x, w, y, alpha) -> int:
        y  = self._draw_section(screen, "ALL-TIME RECORDS", x, w, y, alpha)
        s  = student.stats
        ps = s["peak_stress"]
        lh = s["lowest_health"]
        pm = s["peak_motivation"]
        rows = [
            ("Peak Stress",
             f"{ps}",
             self._C_BAD  if ps > 80 else
             self._C_WARN if ps > 60 else self._C_GOOD),
            ("Lowest Health",
             f"{lh}",
             self._C_BAD  if lh < 30 else
             self._C_WARN if lh < 50 else self._C_GOOD),
            ("Peak Motivation",
             f"{pm}",
             self._C_GOOD if pm > 70 else self._C_WARN),
        ]
        for label, value, color in rows:
            y = self._draw_key_value(screen, label, value, x, w, y, alpha, color)
        return y

    # ── Private drawing helpers ──────────────────────────────────────────

    def _draw_key_value(self, screen, label: str, value: str,
                        x: int, w: int, y: int,
                        alpha: int, value_color: tuple) -> int:
        lbl_surf = self._f_body.render(label, True,
                                        self._alpha_color(self._C_TEXT, alpha))
        val_surf = self._f_body.render(value, True,
                                        self._alpha_color(value_color, alpha))
        screen.blit(lbl_surf, (x, y))
        screen.blit(val_surf, (x + w - val_surf.get_width(), y))
        return y + lbl_surf.get_height() + 6

    def _draw_mini_bar(self, screen, x: int, w: int, y: int,
                       fraction: float, color: tuple, alpha: int) -> int:
        bar_h = 5
        bg = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        bg.fill((*self._C_DIVIDER, alpha))
        screen.blit(bg, (x, y))
        fill_w = int(w * max(0.0, min(fraction, 1.0)))
        if fill_w > 0:
            fill = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            fill.fill((*color, alpha))
            screen.blit(fill, (x, y))
        return y + bar_h + 4

    def _draw_divider(self, screen, x: int, w: int, y: int, alpha: int) -> int:
        y += 6
        surf = pygame.Surface((w, 1), pygame.SRCALPHA)
        surf.fill((*self._C_DIVIDER, alpha))
        screen.blit(surf, (x, y))
        return y + 12

    def _draw_section(self, screen, title: str,
                      x: int, w: int, y: int, alpha: int) -> int:
        lbl = self._f_heading.render(title, True,
                                      self._alpha_color(self._C_GLOW, alpha))
        screen.blit(lbl, (x, y))
        y += lbl.get_height() + 2
        underline = pygame.Surface((w, 1), pygame.SRCALPHA)
        underline.fill((*self._C_GLOW, alpha // 3))
        screen.blit(underline, (x, y))
        return y + 10

    @staticmethod
    def _alpha_color(rgb, alpha: int):
        return (rgb[0], rgb[1], rgb[2])

    def _ensure_fonts(self):
        if self._fonts_loaded:
            return
        self._f_heading    = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._f_body       = pygame.font.Font("assets/fonts/Papernotes.otf", 17)
        self._f_detail     = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._f_tab        = pygame.font.Font("assets/fonts/Papernotes.otf", 14)
        self._fonts_loaded = True