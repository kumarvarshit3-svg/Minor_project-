
 import json
 import os
 from datetime import datetime
 import csv # Imported for potential future CSV export, though TXT is implemented for simplicity
 # Kivy imports
 from kivy.app import App
 from kivy.uix.boxlayout import BoxLayout
 from kivy.uix.gridlayout import GridLayout
 from kivy.uix.label import Label
 from kivy.uix.textinput import TextInput
 from kivy.uix.button import Button
 from kivy.uix.scrollview import ScrollView
 from kivy.uix.popup import Popup
 from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
 from kivy.uix.spinner import Spinner
 from kivy.uix.progressbar import ProgressBar
 from kivy.core.window import Window
 # Import for plotting. Ensure you have installed kivy-garden's matplotlib backend.
 from kivy_garden.matplotlib.FigureCanvasKivyAgg import FigureCanvasKivyAgg
 import matplotlib.pyplot as plt
 class ExpenseData:
      """Handles data persistence, calculations, and all business logic."""
      def __init__(self):
            self.data_ ﬁ le = 'expense_data_v2.json'
            self.expenses = []
            self.balances = {}
            self.goals = {}
            self.categories = ['Food', 'Transport', 'Accommodation', 'Groceries', 'Utilities', 'Entertainment', 'Other']
            self.load_data()
      def load_data(self):
            """Load data from JSON  ﬁ le."""
            try:
                  if os.path.exists(self.data_ ﬁ le):
                        with open(self.data_ ﬁ le, 'r') as  ﬁ le:
                              data = json.load( ﬁ le)
                              self.expenses = data.get('expenses', [])
                              self.balances = data.get('balances', {})
                              self.goals = data.get('goals', {})
            except Exception as e:
                  print(f"Error loading data: {e}")
                  self.expenses, self.balances, self.goals = [], {}, {}
      def save_data(self):
            """Save all data to JSON  ﬁ le."""
            try:
                  data = {
                        'expenses': self.expenses,
                        'balances': self.balances,
                        'goals': self.goals,
                        'last_updated': datetime.now().isoformat()
                  }
                  with open(self.data_ ﬁ le, 'w') as  ﬁ le:                       json.dump(data,  ﬁ le, indent=4)
            except Exception as e:
                  print(f"Error saving data: {e}")
      def add_expense(self, payer, amount, description, category, participants, split_method, split_details):
            """Add new expense with  ﬂ exible splitting and update balances."""
            try:
                  amount =  ﬂ oat(amount)
                  if not all([payer, amount > 0, description, category, participants]):
                        return False, "Payer, Amount, Description, Category, and Participants are required."
            except ValueError:
                  return False, "Please enter a valid amount."
            # Process participants
            participants_list = sorted([p.strip() for p in participants.split(',') if p.strip()])
            if not participants_list:
                  return False, "At least one participant is required."
            # Calculate splits
            try:
                  split_amounts = self._calculate_splits(amount, participants_list, split_method, split_details)
            except ValueError as e:
                  return False, str(e)
             
            # Update balances
            for person, share in split_amounts.items():
                  # Payer's balance increases by what others owe them
                  if person != payer:
                        self.balances.setdefault(payer, 0.0)
                        self.balances[payer] += share
                  # Each participant's balance decreases by their share
                  self.balances.setdefault(person, 0.0)
                  self.balances[person] -= share
            # Add expense record
            expense = {
                  'payer': payer,
                  'amount': amount,
                  'description': description,
                  'category': category,
                  'participants': participants_list,
                  'split_method': split_method,
                  'split_amounts': split_amounts,
                  'date': datetime.now().isoformat(),
            }
            self.expenses.append(expense)
            self.save_data()
            return True, "Expense added successfully."
      def _calculate_splits(self, total_amount, participants, method, details):
            """Helper to calculate splits based on the chosen method."""
            splits = {}
            if method == 'Equally':
                  share = round(total_amount / len(participants), 2)
                  for p in participants:
                        splits[p] = share
                  # Adjust for rounding issues on the last participant
                  splits[participants[-1]] = round(total_amount - share * (len(participants) - 1), 2)
            elif method in ['By Exact Amounts', 'By Percentages', 'By Shares']:
                  parsed_details = {}
                  try:
                        for item in details.split(','):
                              name, value = item.split(':')
                              parsed_details[name.strip()] =  ﬂ oat(v alue.strip())
                  except ValueError:
                        raise ValueError(f"Invalid format for '{method}'. Use 'Name1:Value1, Name2:Value2'.")
                  if set(parsed_details.keys()) != set(participants):
                        raise ValueError("Split details must include all participants, and only them.")                 if method == 'By Exact Amounts':
                        if abs(sum(parsed_details.values()) - total_amount) > 0.01:
                              raise ValueError(f"Exact amounts must sum to the total: ₹{total_amount:.2f}")
                        splits = parsed_details
                   
                  elif method == 'By Percentages':
                        if abs(sum(parsed_details.values()) - 100) > 0.01:
                              raise ValueError("Percentages must sum to 100.")
                        for p, perc in parsed_details.items():
                              splits[p] = round(total_amount * (perc / 100), 2)
                   
                  elif method == 'By Shares':
                        total_shares = sum(parsed_details.values())
                        if total_shares == 0:
                              raise ValueError("Total shares cannot be zero.")
                        for p, share_val in parsed_details.items():
                              splits[p] = round(total_amount * (share_val / total_shares), 2)
             
            # Final check to ensure the calculated splits sum up to the total amount
            if abs(sum(splits.values()) - total_amount) > 0.01:
                    # Distribute rounding difference to the largest shareholder to minimize relative error
                  diff = total_amount - sum(splits.values())
                  if splits:
                        person_to_adjust = max(splits, key=splits.get)
                        splits[person_to_adjust] += diff
            return splits
      def calculate_debts(self):
            """Calculate simpli ﬁ ed debt settlements."""
            debtors = {p: v for p, v in self.balances.items() if v < 0}
            creditors = {p: v for p, v in self.balances.items() if v > 0}
            settlements = []
            for debtor, debt_amount in sorted(debtors.items(), key=lambda x: x[1]):
                  for creditor, credit_amount in sorted(creditors.items(), key=lambda x: x[1], reverse=True):
                        if abs(debt_amount) < 0.01 or credit_amount < 0.01:
                              continue
                         
                        amount_to_settle = round(min(abs(debt_amount), credit_amount), 2)
                        if amount_to_settle > 0:
                              settlements.append({'from': debtor, 'to': creditor, 'amount': amount_to_settle})
                              debtors[debtor] += amount_to_settle
                              creditors[creditor] -= amount_to_settle
                              debt_amount += amount_to_settle
            return settlements
      def settle_all_balances(self):
            """Reset all balances to zero."""
            self.balances = {}
            self.save_data()
       
      def set_goal(self, category, amount):
            """Set or update a spending goal for a category."""
            try:
                  amount =  ﬂ oat(amount)
                  if amount < 0: return False, "Goal amount cannot be negative."
                  self.goals[category] = amount
                  self.save_data()
                  return True, f"Goal for '{category}' set to ₹{amount:.2f}."
            except ValueError:
                  return False, "Invalid amount for goal."
       
      def get_spending_summary_by_category(self):
            """Returns a dict of total spending per category."""
            summary = {cat: 0.0 for cat in self.categories}
            for expense in self.expenses:
                  cat = expense.get('category', 'Other')
                  summary[cat] = summary.get(cat, 0.0) + expense['amount']           return {k: v for k, v in summary.items() if v > 0}
       
      def get_total_paid_by_person(self):
            """Returns a dict of total amount paid by each person."""
            summary = {}
            for expense in self.expenses:
                  payer = expense['payer']
                  summary[payer] = summary.get(payer, 0.0) + expense['amount']
            return summary
       
      def export_summary(self):
            """Generates a string summary and saves it to a text  ﬁ le. """
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
             ﬁ lename = f'expense_report_{timestamp}.txt'
             
            try:
                  with open( ﬁ lename, 'w') as f:
                        f.write("--- Expense Report ---\n")
                        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write("--- All Expenses ---\n")
                        for ex in self.expenses:
                              dt = datetime.fromisoformat(ex['date']).strftime('%Y-%m-%d')
                              f.write(f"[{dt}] {ex['description']} ({ex['category']}): ₹{ex['amount']:.2f} paid by {ex['payer']}\n")
                         
                        f.write("\n--- Final Balances ---\n")
                        for person, bal in self.balances.items():
                              status = "gets back" if bal > 0 else "owes"
                              f.write(f"{person}: {status} ₹{abs(bal):.2f}\n")
                         
                        f.write("\n--- Settlement Plan ---\n")
                        debts = self.calculate_debts()
                        if debts:
                              for debt in debts:
                                    f.write(f"{debt['from']} should pay {debt['to']} ₹{debt['amount']:.2f}\n")
                        else:
                              f.write("All balances are settled.\n")
                  return True, f"Report saved to { ﬁ lename}"
            except Exception as e:
                  return False, f"Error exporting  ﬁ le: {e}"
 class AddExpenseScreen(Screen):
      def __init__(self, expense_data, **kwargs):
            super().__init__(**kwargs)
            self.expense_data = expense_data
            self.build_ui()
      def build_ui(self):
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            layout.add_widget(Label(text='Add New Expense', size_hint_y=None, height=50, font_size='24sp'))
             
            form_grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
            form_grid.bind(minimum_height=form_grid.setter('height'))
             
            # Payer
            form_grid.add_widget(Label(text='Payer:', height=40, size_hint_y=None))
            self.payer_input = TextInput(multiline=False, height=40, size_hint_y=None)
            form_grid.add_widget(self.payer_input)
             
            # Amount
            form_grid.add_widget(Label(text='Amount (₹):', height=40, size_hint_y=None))
            self.amount_input = TextInput(input_ ﬁ lter=' ﬂ oat', multiline=False, height=40, size_hint_y=None)
            form_grid.add_widget(self.amount_input)
             
            # Category
            form_grid.add_widget(Label(text='Category:', height=40, size_hint_y=None))
            self.category_spinner = Spinner(text='Select Category', values=self.expense_data.categories, height=40, size_hint_y=None)
            form_grid.add_widget(self.category_spinner)           # Description
            form_grid.add_widget(Label(text='Description:', height=40, size_hint_y=None))
            self.description_input = TextInput(multiline=False, height=40, size_hint_y=None)
            form_grid.add_widget(self.description_input)
            # Participants
            form_grid.add_widget(Label(text='Participants\n(comma-separated):', height=60, size_hint_y=None))
            self.participants_input = TextInput(multiline=True, height=60, size_hint_y=None)
            form_grid.add_widget(self.participants_input)
            # Split Method
            form_grid.add_widget(Label(text='Split Method:', height=40, size_hint_y=None))
            self.split_method_spinner = Spinner(
                  text='Equally',
                  values=('Equally', 'By Exact Amounts', 'By Percentages', 'By Shares'),
                  height=40, size_hint_y=None)
            self.split_method_spinner.bind(text=self.on_split_method_change)
            form_grid.add_widget(self.split_method_spinner)
            # Split Details
            self.split_details_label = Label(text='Details (if not equal):', height=60, size_hint_y=None)
            form_grid.add_widget(self.split_details_label)
            self.split_details_input = TextInput(multiline=True, height=60, size_hint_y=None, hint_text="e.g., Alice:50, Bob:30")
            form_grid.add_widget(self.split_details_input)
            layout.add_widget(form_grid)
            layout.add_widget(BoxLayout(size_hint_y=1)) # Spacer
            # Buttons
            btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
            add_btn = Button(text='Add Expense', on_press=self.add_expense)
            clear_btn = Button(text='Clear Form', on_press=self.clear_form)
            btn_layout.add_widget(add_btn)
            btn_layout.add_widget(clear_btn)
             
            layout.add_widget(btn_layout)
            self.add_widget(layout)
      def on_split_method_change(self, spinner, text):
            """Update UI based on split method."""
            if text == 'Equally':
                  self.split_details_input.disabled = True
                  self.split_details_input.background_color = (0.8, 0.8, 0.8, 1)
                  self.split_details_input.text = ""
            else:
                  self.split_details_input.disabled = False
                  self.split_details_input.background_color = (1, 1, 1, 1)
      def add_expense(self, instance):
            success, message = self.expense_data.add_expense(
                  self.payer_input.text,
                  self.amount_input.text,
                  self.description_input.text,
                  self.category_spinner.text,
                  self.participants_input.text,
                  self.split_method_spinner.text,
                  self.split_details_input.text
            )
            self.show_popup("Success" if success else "Error", message)
            if success:
                  self.clear_form(None)
      def clear_form(self, instance):
            self.payer_input.text = ''
            self.amount_input.text = ''
            self.description_input.text = ''
            self.participants_input.text = ''
            self.category_spinner.text = 'Select Category'
            self.split_method_spinner.text = 'Equally'           self.split_details_input.text = ''
      def show_popup(self, title, message):
            popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
            popup.open()
 class ExpenseListScreen(Screen):
      def __init__(self, expense_data, **kwargs):
            super().__init__(**kwargs)
            self.expense_data = expense_data
            self.build_ui()
       
      def build_ui(self):
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            header = BoxLayout(size_hint_y=None, height=50)
            header.add_widget(Label(text='Expense History', font_size='24sp'))
            refresh_btn = Button(text='Refresh', size_hint_x=None, width=120, on_press=self.refresh_list)
            header.add_widget(refresh_btn)
            layout.add_widget(header)
            scroll = ScrollView()
            self.expense_list = GridLayout(cols=1, size_hint_y=None, spacing=10)
            self.expense_list.bind(minimum_height=self.expense_list.setter('height'))
            scroll.add_widget(self.expense_list)
            layout.add_widget(scroll)
            self.add_widget(layout)
      def refresh_list(self, instance):
            self.expense_list.clear_widgets()
            if not self.expense_data.expenses:
                  self.expense_list.add_widget(Label(text='No expenses recorded yet', size_hint_y=None, height=40))
                  return
             
            for expense in reversed(self.expense_data.expenses):
                  date_str = datetime.fromisoformat(expense['date']).strftime('%b %d, %Y')
                  main_text = f"[{expense['category']}] {expense['description']}: ₹{expense['amount']:.2f}"
                  detail_text = f"Paid by {expense['payer']} on {date_str} | Split: {expense['split_method']}"
                   
                  entry = BoxLayout(orientation='vertical', size_hint_y=None, height=60, padding=(10, 5))
                  entry.add_widget(Label(text=main_text, halign='left', valign='middle', text_size=(Window.width*0.8, None)))
                  entry.add_widget(Label(text=detail_text, font_size='12sp', color=(0.4,0.4,0.4,1), halign='left', valign='middle', text_size=
 ( Window .width*0.8, None)))
                  self.expense_list.add_widget(entry)
 class BalanceScreen(Screen):
      def __init__(self, expense_data, **kwargs):
            super().__init__(**kwargs)
            self.expense_data = expense_data
            self.build_ui()
       
      def build_ui(self):
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            header = BoxLayout(size_hint_y=None, height=50)
            header.add_widget(Label(text='Balances & Settlements', font_size='24sp'))
            refresh_btn = Button(text='Refresh', size_hint_x=None, width=120, on_press=self.refresh_balances)
            header.add_widget(refresh_btn)
            layout.add_widget(header)
            self.balance_list = GridLayout(cols=1, size_hint_y=None, spacing=10)
            self.balance_list.bind(minimum_height=self.balance_list.setter('height'))
            scroll = ScrollView()
            scroll.add_widget(self.balance_list)
            layout.add_widget(scroll)
            btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
            settle_plan_btn = Button(text='Show Settlement Plan', on_press=self.show_settlement_plan)
            settle_all_btn = Button(text='Settle All Balances', on_press=self.con ﬁ rm_settle_all)
            export_btn = Button(text='Export Summary', on_press=self.export_summary)           btn_layout.add_widget(settle_plan_btn)
            btn_layout.add_widget(settle_all_btn)
            btn_layout.add_widget(export_btn)
            layout.add_widget(btn_layout)
            self.add_widget(layout)
       
      def refresh_balances(self, instance):
            self.balance_list.clear_widgets()
            balances = self.expense_data.balances
            if not any(abs(bal) > 0.01 for bal in balances.values()):
                  self.balance_list.add_widget(Label(text='All balances are settled.', size_hint_y=None, height=40))
                  return
            for person, balance in sorted(balances.items()):
                    if abs(balance) > 0.01:
                        color = (0.1, 0.6, 0.1, 1) if balance > 0 else (0.8, 0.2, 0.2, 1)
                        status = "is owed" if balance > 0 else "owes"
                        text = f"{person} {status} ₹{abs(balance):.2f}"
                        self.balance_list.add_widget(Label(text=text, color=color, size_hint_y=None, height=40))
      def show_settlement_plan(self, instance):
            debts = self.expense_data.calculate_debts()
            if not debts:
                  self.show_popup("Settlement Plan", "All balances are already settled!")
                  return
            debt_text = "\n".join([f"{d['from']} owes {d['to']}: ₹{d['amount']:.2f}" for d in debts])
            self.show_popup("Settlement Plan", debt_text)
       
      def con ﬁ rm_settle_all(self, instance):
            if not self.expense_data.balances:
                  self.show_popup("Info", "There are no balances to settle.")
                  return
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            content.add_widget(Label(text='Are you sure you want to clear all balances?\nThis action cannot be undone.'))
            btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
            con ﬁ rm_btn = Button(text='Yes, Settle All')
            cancel_btn = Button(text='Cancel')
            btn_box.add_widget(con ﬁ rm_btn)
            btn_box.add_widget(cancel_btn)
            content.add_widget(btn_box)
             
            popup = Popup(title='Con ﬁ rm Settlement', content=content, size_hint=(0.8, 0.5))
            con ﬁ rm_btn.bind(on_pr ess=lambda x: self.execute_settlement(popup))
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()
             
      def execute_settlement(self, popup):
            popup.dismiss()
            self.expense_data.settle_all_balances()
            self.refresh_balances(None)
            self.show_popup("Success", "All balances have been settled!")
      def export_summary(self, instance):
            success, message = self.expense_data.export_summary()
            self.show_popup("Export Status", message)
      def show_popup(self, title, message):
            popup = Popup(title=title, content=Label(text=message, halign='center'), size_hint=(0.8, 0.5))
            popup.open()
 class AnalyticsScreen(Screen):
      def __init__(self, expense_data, **kwargs):
            super().__init__(**kwargs)
            self.expense_data = expense_data
            plt.style.use('seaborn-v0_8-pastel') # Use a nice style for plots
            self.build_ui()
      def build_ui(self):           self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
             
            header = BoxLayout(size_hint_y=None, height=50)
            header.add_widget(Label(text='Analytics', font_size='24sp'))
            refresh_btn = Button(text='Refresh', size_hint_x=None, width=120, on_press=self.refresh_charts)
            header.add_widget(refresh_btn)
            self.main_layout.add_widget(header)
            # Placeholder for charts
            self.chart_layout = BoxLayout(orientation='vertical')
            self.main_layout.add_widget(self.chart_layout)
             
            self.add_widget(self.main_layout)
      def refresh_charts(self, instance=None):
            self.chart_layout.clear_widgets()
             
            if not self.expense_data.expenses:
                  self.chart_layout.add_widget(Label(text="No data to display. Add some expenses  ﬁ rst. "))
                  return
                   
            # Chart 1: Spending by Category (Pie Chart)
            cat_summary = self.expense_data.get_spending_summary_by_category()
            if cat_summary:
                   ﬁ g1, ax1 = plt.subplots()
                  labels = cat_summary.keys()
                  sizes = cat_summary.values()
                  ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                  ax1.axis('equal')   # Equal aspect ratio ensures that pie is drawn as a circle.
                  ax1.set_title('Spending by Category')
                  self.chart_layout.add_widget(FigureCanvasKivyAgg( ﬁ g1))
            # Chart 2: Total Paid by Person (Bar Chart)
            person_summary = self.expense_data.get_total_paid_by_person()
            if person_summary:
                   ﬁ g2, ax2 = plt.subplots()
                  names = list(person_summary.keys())
                  values = list(person_summary.values())
                  ax2.bar(names, values)
                  ax2.set_ylabel('Amount Paid (₹)')
                  ax2.set_title('Total Paid by Each Person')
                  plt.setp(ax2.get_xticklabels(), rotation=30, horizontalalignment='right')
                   ﬁ g2.tight_la y out()
                  self.chart_layout.add_widget(FigureCanvasKivyAgg( ﬁ g2))
 class GoalsScreen(Screen):
      def __init__(self, expense_data, **kwargs):
            super().__init__(**kwargs)
            self.expense_data = expense_data
            self.build_ui()
      def build_ui(self):
            layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            header = BoxLayout(size_hint_y=None, height=50)
            header.add_widget(Label(text='Spending Goals', font_size='24sp'))
            refresh_btn = Button(text='Refresh', size_hint_x=None, width=120, on_press=self.refresh_goals)
            header.add_widget(refresh_btn)
            layout.add_widget(header)
             
            # Goal Setting Area
            set_goal_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
            self.goal_cat_spinner = Spinner(text='Category', values=self.expense_data.categories)
            self.goal_amount_input = TextInput(hint_text='Goal Amount (₹)', input_ ﬁ lter=' ﬂ oat')
            set_goal_btn = Button(text='Set Goal', size_hint_x=0.4)
            set_goal_btn.bind(on_press=self.set_goal)
            set_goal_layout.add_widget(self.goal_cat_spinner)
            set_goal_layout.add_widget(self.goal_amount_input)
            set_goal_layout.add_widget(set_goal_btn)
            layout.add_widget(set_goal_layout)            
            # Goal Progress Area
            scroll = ScrollView()
            self.goals_list = GridLayout(cols=1, size_hint_y=None, spacing=15)
            self.goals_list.bind(minimum_height=self.goals_list.setter('height'))
            scroll.add_widget(self.goals_list)
            layout.add_widget(scroll)
            self.add_widget(layout)
      def refresh_goals(self, instance=None):
            self.goals_list.clear_widgets()
            goals = self.expense_data.goals
            spending = self.expense_data.get_spending_summary_by_category()
            if not goals:
                  self.goals_list.add_widget(Label(text="No goals set. Set one above!", size_hint_y=None, height=40))
                  return
            for category, goal_amount in goals.items():
                  spent_amount = spending.get(category, 0.0)
                  progress = (spent_amount / goal_amount) * 100 if goal_amount > 0 else 0
                   
                  goal_box = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
                   
                  label_text = f"{category}: ₹{spent_amount:.2f} / ₹{goal_amount:.2f}"
                  goal_label = Label(text=label_text, halign='left', text_size=(Window.width*0.8, None))
                   
                  progress_bar = ProgressBar(max=100, value=progress)
                   
                  goal_box.add_widget(goal_label)
                  goal_box.add_widget(progress_bar)
                  self.goals_list.add_widget(goal_box)
      def set_goal(self, instance):
            category = self.goal_cat_spinner.text
            amount = self.goal_amount_input.text
            if category == 'Category' or not amount:
                  self.show_popup("Error", "Please select a category and enter an amount.")
                  return
                   
            success, message = self.expense_data.set_goal(category, amount)
            self.show_popup("Status", message)
            if success:
                  self.goal_amount_input.text = ""
                  self.refresh_goals()
      def show_popup(self, title, message):
            popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
            popup.open()
 class ExpenseTrackerApp(App):
      def build(self):
            Window.clearcolor = (0.98, 0.98, 0.98, 1) # A lighter background
            self.expense_data = ExpenseData()
             
            sm = ScreenManager(transition=FadeTransition(duration=0.2))
             
            # Add all screens to the manager
            sm.add_widget(AddExpenseScreen(self.expense_data, name='add'))
            sm.add_widget(ExpenseListScreen(self.expense_data, name='list'))
            sm.add_widget(BalanceScreen(self.expense_data, name='balance'))
            sm.add_widget(AnalyticsScreen(self.expense_data, name='analytics'))
            sm.add_widget(GoalsScreen(self.expense_data, name='goals'))
             
            main_layout = BoxLayout(orientation='vertical')
             
            # Bottom Navigation Bar
            nav_layout = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=5)
            nav_buttons = {                 'add': Button(text='Add'),
                  'list': Button(text='History'),
                  'balance': Button(text='Balances'),
                  'analytics': Button(text='Analytics'),
                  'goals': Button(text='Goals')
            }
             
            for screen_name, button in nav_buttons.items():
                  button.bind(on_press=lambda x, name=screen_name: self.switch_screen(sm, name))
                  nav_layout.add_widget(button)
             
            main_layout.add_widget(sm)
            main_layout.add_widget(nav_layout)
             
            # Initial refresh
            sm.get_screen('list').refresh_list(None)
            return main_layout
       
      def switch_screen(self, screen_manager, screen_name):
            screen_manager.current = screen_name
            # Refresh screen content when switching to it
            current_screen = screen_manager.get_screen(screen_name)
            if hasattr(current_screen, 'refresh_list'):
                  current_screen.refresh_list(None)
            elif hasattr(current_screen, 'refresh_balances'):
                  current_screen.refresh_balances(None)
            elif hasattr(current_screen, 'refresh_charts'):
                  current_screen.refresh_charts(None)
            elif hasattr(current_screen, 'refresh_goals'):
                  current_screen.refresh_goals(None)
 if __name__ == '__main__':
          ExpenseTrackerApp().run()
