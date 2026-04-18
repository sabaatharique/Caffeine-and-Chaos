import math
import random

class Student:
    def __init__(self, type_mult: float = 1.0):
        self.type_mult = type_mult

        # Status bars
        self.sleep = 90
        self.health = 80
        self.stress = 30
        self.motivation = 60
        self.hunger = 50

        # Hunger tracking
        self.hours_since_last_meal = 0.0  # resets to 0 when eating
        self.hunger_decay_rate = 2.0      # base value added to hunger per half-life period
        self.hunger_half_life = 2.0       # hours until decay period doubles

        # WiFi state
        self.wifi_down = False            # set True during an outage
        self.wifi_knowledge_penalty = 0.5 # multiplier on knowledge gain when wifi is down
        self.wifi_stress_penalty = 4.0    # extra stress per hour of studying without wifi

        # Academic tracking
        self.attendance = 0

        # Internal tracking
        self.consecutive_stress_days = 0
        self.burnout_days_remaining = 5

        # Sickness tracking
        self.is_sick = False
        self.sick_days_remaining = 0

        # Rolling history (last 5 days) for computing sickness probability
        self._stress_history: list = []
        self._health_history: list = []
        self._HISTORY_WINDOW = 5          # days to look back
        self._SICKNESS_BASE_PROB = 0.005  # 0.5% daily baseline
        self._SICKNESS_MAX_PROB  = 0.10   # hard cap at 10%
        self._RECOVERY_PROB      = 0.40   # 40% chance to recover each sick day (~2.5 day expected illness)

        # Action rates
        self.study_knowledge_rate = 1 * type_mult
        self.study_sleep_rate =  8    
        self.study_stress_rate = 10   
        self.study_health_rate = 5   

        self.rest_sleep_rate = 10   
        self.rest_stress_rate = 5    
        self.rest_health_rate = 3    
        self.rest_health_rate = 3    

        self.relax_stress_rate = 8
        self.relax_sleep_rate = 3
        self.relax_motivation_rate = 5
        self.relax_health_rate = 5       # health gained per hour of relaxing

        self.eat_health_gain = 10    
        self.eat_hunger_reduction = 40    
        self.eat_stress_reduction = 5    

        self.coffee_sleep_gain = 10    
        self.coffee_health_loss = 7    
        self.coffee_stress_gain = 3    

        self.class_knowledge_rate = 2     
        self.class_stress_rate = 3     
        self.class_sleep_loss = 5     

        # Action enabled
        self.action_status = {
            'study': True,
            'sleep': True,
            'relax': True,
            'eat': True,
            'coffee': True,
            'attend_class': True,
        }
        self.update_action_status()  # Initial update

    def update_action_status(self):
        self.action_status['study'] = self.sleep > 0 and self.health > 0
        self.action_status['sleep'] = self.sleep < 100
        self.action_status['relax'] = True
        self.action_status['eat'] = self.health < 100 or self.hunger > 0
        self.action_status['coffee'] = self.sleep < 100 and self.health > 0
        # self.action_status['attend_class'] = self.sleep > 0

    def clamp(self):
        messages = []
        # Keep values within limits
        self.sleep = max(0, min(100, self.sleep))
        self.health = max(0, min(100, self.health))
        self.stress = max(0, min(100, self.stress))
        self.motivation = max(0, min(100, self.motivation))
        self.hunger = max(0, min(100, self.hunger))
        self.attendance = max(0, min(100, self.attendance))


        if self.sleep < 10:
            messages.append("Warning: Sleep is critically low!")
        if self.sleep == 100:
            messages.append("Sleep maxxed out!")

        if self.health < 10:
            messages.append("Warning: Health is critically low!")
        if self.health == 100:
            messages.append("Health maxxed out!")
        
        if self.motivation < 10:
            messages.append("Warning: Motivation is critically low!")

        if self.stress > 90:
            messages.append("Warning: Stress is critically high!")
        
        self.update_action_status()
        return messages

    # Sickness helpers 

    def _record_daily_history(self):
        """Snapshot today's stress & health into rolling history."""
        self._stress_history.append(self.stress)
        self._health_history.append(self.health)
        # Keep only the last N days
        if len(self._stress_history) > self._HISTORY_WINDOW:
            self._stress_history.pop(0)
        if len(self._health_history) > self._HISTORY_WINDOW:
            self._health_history.pop(0)

    def _compute_sickness_prob(self) -> float:
        """Return today's Bernoulli probability of falling sick."""
        import events
        return events.compute_sickness_prob(
            self._stress_history,
            self._health_history,
            self._SICKNESS_BASE_PROB,
            self._SICKNESS_MAX_PROB
        )

    def _generate_sick_duration(self) -> int:
        """Sample illness duration from a geometric distribution."""
        import events
        return events.generate_sick_duration(self._RECOVERY_PROB)

    @property
    def sick_active(self) -> bool:
        """True while the student is sick (mirrors burnout_active pattern)."""
        return self.is_sick

    def end_of_day(self):
        messages = []

        # Daily changes in state
        if self.stress > 70:
            self.consecutive_stress_days += 1
        else:
            self.consecutive_stress_days = 0

        if self.burnout_days_remaining > 0:
            self.burnout_days_remaining -= 1
            if self.burnout_days_remaining == 0:
                messages.append("You have recovered from burnout!")

        if self.burnout_check():
            self.trigger_burnout()
            messages.append("Burnout! Your stats have taken a hit.")

        # ── Sickness logic ────────────────────────────────────────────────────
        # Always record today before checking onset so history is up-to-date
        self._record_daily_history()

        if self.is_sick:
            # Geometric recovery trial each sick day
            if random.random() < self._RECOVERY_PROB:
                self.is_sick = False
                self.sick_days_remaining = 0
                messages.append("[RECOVERED] You're no longer sick. Welcome back!")
            else:
                self.sick_days_remaining = max(0, self.sick_days_remaining - 1)
                # Daily passive effect while sick: health drains a little
                self.health -= 5
                self.stress += 5
                messages.append(f"[SICK] Health -5, Stress +5. Still feeling unwell...")
        else:
            # Bernoulli trial for new sickness onset
            p = self._compute_sickness_prob()
            
            # Request: If health becomes 0 at any point, then player should become sick
            exhausted = self.health <= 0
            
            if exhausted or random.random() < p:
                self.is_sick = True
                self.sick_days_remaining = self._generate_sick_duration()
                # Immediate onset penalty
                self.health -= 10
                self.stress += 10
                if exhausted:
                    messages.append(f"[SICK!] Your health hit zero! You've collapsed from exhaustion.\nSick for {self.sick_days_remaining} days.")
                else:
                    messages.append(f"[SICK!] You've fallen ill for {self.sick_days_remaining} days!\nHealth -10, Stress +10.")
                messages.append("[SICK!] Study efficiency halved. Classes will be missed.")

        messages.extend(self.clamp())
        return messages

    def attend_class(self, course, avg_knowledge=0.0):
        messages = []
        if not self.action_status['attend_class']:
            messages.append("You are too tired to attend class.")
            return messages

        # Always count this as an occurred class slot (whether attended or missed)
        course.occurred_classes += 1

        if self.is_sick:
            messages.append(f"You're too sick to attend {course.name}. Class missed.")
            # Still counts against attendance — you really weren't there
            return messages

        course.attended_classes += 1
        self.attendance += 1
        course.add_knowledge(self.class_knowledge_rate)
        self.sleep -= self.class_sleep_loss
        self.stress += self.class_stress_rate
        self.motivation += 3

        messages.append(f"Attended {course.name}. Knowledge +{self.class_knowledge_rate}.")
        messages.extend(self.clamp())
        return messages

    def study(self, course, hours=2.0, avg_knowledge=30.0, wifi_penalty=False):
        messages = []
        if not self.action_status['study']:
            if self.health <= 0:
                messages.append("You are too ill to study. Rest or relax to regain your health!")
            else:
                messages.append("You are too tired to study.")
            return messages
        # Study efficiency depends on current state (using average knowledge for global efficiency)
        efficiency = (self.sleep + self.health + (100 - self.stress) + (100 - self.motivation) + avg_knowledge) / 500
        knowledge_mult = self.wifi_knowledge_penalty if wifi_penalty else 1.0
        if self.is_sick:
            knowledge_mult *= 0.5   # sickness halves effective learning

        gain = hours * self.study_knowledge_rate * efficiency * knowledge_mult
        course.add_knowledge(gain)

        self.sleep  -= hours * self.study_sleep_rate
        self.stress += hours * self.study_stress_rate
        if wifi_penalty:
            self.stress += hours * self.wifi_stress_penalty
        self.health -= hours * self.study_health_rate

        messages.extend(self.clamp())
        # If studying drained health to 0, trigger immediate sickness
        messages.extend(self.check_health_collapse())
        return messages

    def rest(self, hours=1.0):
        messages = []
        if not self.action_status['sleep']:
            messages.append("You are well rested.")
            return messages
        self.sleep += hours * self.rest_sleep_rate
        self.stress -= hours * self.rest_stress_rate
        self.health += hours * self.rest_health_rate

        messages.extend(self.clamp())
        return messages
    
    def apply_hunger_decay(self, elapsed_hours):
        old_total = self.hours_since_last_meal
        new_total = old_total + elapsed_hours
        self.hours_since_last_meal = new_total

        penalty_before = self.hunger_decay_rate * (math.pow(2, old_total / self.hunger_half_life) - 1)
        penalty_after  = self.hunger_decay_rate * (math.pow(2, new_total / self.hunger_half_life) - 1)
        delta = penalty_after - penalty_before  # incremental loss this tick

        messages = []
        if delta > 0:
            self.hunger += delta
            if new_total >= 6:
                messages.append(f"You're starving!")
            elif new_total >= 3:
                messages.append(f"You're getting hungry...")
        
        messages.extend(self.clamp())
        return messages

    def eat(self):
        messages = []
        if not self.action_status['eat']:
             # This msg might not trigger if hunger > 0
             messages.append("You aren't hungry.")
             return messages
        self.health += self.eat_health_gain
        self.hunger -= self.eat_hunger_reduction
        self.stress -= self.eat_stress_reduction
        self.hours_since_last_meal = 0.0  # reset hunger timer

        messages.extend(self.clamp())
        return messages

    def drink_coffee(self):
        messages = []
        if not self.action_status['coffee']:
            if self.health < 10:
                 messages.append("Your health is too low to drink coffee.")
            else:
                 messages.append("You are already wide awake.")
            return messages
        self.sleep += self.coffee_sleep_gain
        self.health -= self.coffee_health_loss
        self.stress += self.coffee_stress_gain

        messages.extend(self.clamp())
        return messages

    def take_break(self, hours=1.0):
        messages = []
        self.stress -= hours * self.relax_stress_rate
        self.sleep  -= hours * self.relax_sleep_rate
        self.motivation += hours * self.relax_motivation_rate
        self.health += hours * self.relax_health_rate   # relaxing restores health

        messages.extend(self.clamp())
        return messages

    def check_health_collapse(self):
        """Call after any health-draining action.
        If health just hit 0, trigger immediate sickness so the player is
        forced to rest/relax before studying again.
        Returns a list of messages (empty if nothing happened).
        """
        messages = []
        if not self.is_sick and self.health <= 0:
            self.is_sick = True
            self.sick_days_remaining = self._generate_sick_duration()
            self.stress += 15          # exhaustion spike
            messages.append("[SICK!] Your health hit zero! You've collapsed from exhaustion.")
            messages.append("[SICK!] You MUST rest or relax. Study and class are blocked until you recover.")
            messages.extend(self.clamp())
        return messages

    def max_hours(self, action):
        limits = [24.0]

        if action == 'study':
            # sleep  -= hours * study_sleep_rate   →  max before 0
            if self.sleep > 0:
                limits.append(self.sleep / self.study_sleep_rate)
            # health -= hours * study_health_rate  →  max before 0
            if self.health > 0:
                limits.append(self.health / self.study_health_rate)
            # stress += hours * study_stress_rate  →  max before 100
            if self.stress < 100:
                limits.append((100 - self.stress) / self.study_stress_rate)

        elif action == 'sleep':
            # sleep  += hours * rest_sleep_rate    →  max before 100
            if self.sleep < 100:
                limits.append((100 - self.sleep) / self.rest_sleep_rate)
            # no longer global knowledge limit

        elif action == 'relax':
            # No limits for relaxing
            pass

        # Return the precise float limit (no floor), minimum 1 minute (1/60 h)
        return max(1 / 60, min(limits))

    def burnout_check(self):
        # Return true if burnout occurs
        return self.consecutive_stress_days >= 5

    def trigger_burnout(self):
        # self.knowledge -= 5  # No longer global knowledge
        self.motivation -= 20
        self.health -= 10
        self.stress += 10
        self.sleep -= 15

        self.burnout_days_remaining = 2
        self.consecutive_stress_days = 0
        self.clamp()
