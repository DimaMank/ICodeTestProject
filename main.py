import sqlite3
import datetime

# Создание базы данных
conn = sqlite3.connect("contracts_projects.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT,
        created_date DATETIME
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY,
        name TEXT,
        created_date DATETIME,
        status TEXT,
        signing_date DATETIME,
        project_id INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
''')

conn.commit()

class Contract:
    def __init__(self, name, project_id=None):
        self.name = name
        self.created_date = datetime.datetime.now()
        self.status = "Черновик"
        self.signing_date = None
        self.project_id = project_id
        self.id = None

    def confirm_contract(self, project):
        if self.status == "Черновик":
            self.status = "Активен"
            self.signing_date = datetime.datetime.now()
            self.project_id = project.id

    def finish_contract(self):
        if self.project_id:
            self.project_id = None
        self.status = "Завершен"
        self.save_to_db()

    def save_to_db(self):
        conn = sqlite3.connect("contracts_projects.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contracts (name, created_date, status, signing_date, project_id) VALUES (?, ?, ?, ?, ?)",
                       (self.name, self.created_date, self.status, self.signing_date, self.project_id))
        conn.commit()
        self.id = cursor.lastrowid

class Project:
    def __init__(self, name):
        self.name = name
        self.created_date = datetime.datetime.now()
        self.contracts = []
        self.id = None

    def add_contract(self, contract):
        if contract.status == "Активен" and not self.has_active_contract() and not contract.project_id:
            if contract not in self.contracts:
                self.contracts.append(contract)
                contract.project_id = self.id
                contract.save_to_db()
                return True
        return False

    def has_active_contract(self):
        for contract in self.contracts:
            if contract.status == "Активен":
                return True
        return False

    def remove_contract(self, contract):
        if contract in self.contracts:
            self.contracts.remove(contract)
            contract.project_id = None
            contract.save_to_db()

    def save_to_db(self):
        conn = sqlite3.connect("contracts_projects.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (name, created_date) VALUES (?, ?)",
                       (self.name, self.created_date))
        conn.commit()
        self.id = cursor.lastrowid

def create_contract(projects):
    if not projects:
        print("Сначала создайте проекты.")
        return None

    print("Список проектов:")
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project.name}")

    project_index = int(input("Выберите проект для договора: ")) - 1
    if 0 <= project_index < len(projects):
        project = projects[project_index]
        name = input("Введите название договора: ")

        # Проверяем, что договор с таким названием не существует
        existing_contracts = [contract.name for contract in project.contracts]
        if name in existing_contracts:
            print(f"Договор с названием '{name}' уже существует.")
            return None

        contract = Contract(name)
        project.add_contract(contract)
        print(f"Договор '{contract.name}' создан и привязан к проекту '{project.name}'.")
        return contract
    else:
        print("Недопустимый выбор.")
        return None

def create_project():
    name = input("Введите название проекта: ")
    return Project(name)

def list_projects(projects):
    print("Список проектов:")
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project.name}")

def list_contracts(contracts):
    print("Список договоров:")
    for idx, contract in enumerate(contracts, 1):
        if contract.project_id:
            print(f"{idx}. {contract.name} ({contract.status}) - Проект: {get_project_name(contract.project_id)}")
        else:
            print(f"{idx}. {contract.name} ({contract.status}) - Проект: Нет")

def get_project_name(project_id):
    conn = sqlite3.connect("contracts_projects.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return "Проект не найден"

def main_menu():
    projects = []
    contracts = []

    while True:
        print("Главное меню:")
        print("1. Создать проект")
        print("2. Создать договор")
        print("3. Подтвердить договор")
        print("4. Завершить договор")
        print("5. Просмотреть список проектов")
        print("6. Просмотреть список договоров")
        print("7. Завершить работу с программой")

        choice = input("Выберите действие: ")

        if choice == "1":
            project = create_project()
            if project:
                projects.append(project)
                project.save_to_db()
                print(f"Проект '{project.name}' создан и сохранен в базе данных.")

        elif choice == "2":
            contract = create_contract(projects)
            if contract:
                contracts.append(contract)
                contract.save_to_db()
                print(f"Договор '{contract.name}' создан и сохранен в базе данных.")

        elif choice == "3":
            for idx, contract in enumerate(contracts, 1):
                print(f"{idx}. {contract.name} ({contract.status})")
            index = int(input("Выберите договор для подтверждения: ")) - 1
            if 0 <= index < len(contracts):
                contract = contracts[index]
                for idx, project in enumerate(projects, 1):
                    print(f"{idx}. {project.name}")
                project_index = int(input("Выберите проект для договора: ")) - 1
                if 0 <= project_index < len(projects):
                    project = projects[project_index]
                    contract.confirm_contract(project)
                    contract.save_to_db()
                    print(f"Договор '{contract.name}' подтвержден и привязан к проекту '{project.name}'.")
                else:
                    print("Недопустимый выбор проекта.")
            else:
                print("Недопустимый выбор договора.")


        elif choice == "4":
            print("Список доступных для завершения договоров:")
            for idx, contract in enumerate(contracts, 1):
                if contract.status == "Активен":
                    print(f"{idx}. {contract.name} ({contract.status})")
            index = int(input("Выберите договор для завершения: ")) - 1
            if 0 <= index < len(contracts):
                contract = contracts[index]
                contract.finish_contract()
                contract.save_to_db()
                print(f"Договор '{contract.name}' завершен.")
            else:
                print("Недопустимый выбор договора.")

        elif choice == "5":
            list_projects(projects)

        elif choice == "6":
            list_contracts(contracts)

        elif choice == "7":
            break

if __name__ == "__main__":
    main_menu()
