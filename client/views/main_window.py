from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Iterable

from pydantic import ValidationError

from app.models import (
    AAV,
    AAVCreate,
    AAVUpdate,
    LearnerCreate,
    RegleProgression,
    TentativeCreate,
    TypeAAV,
    TypeEvaluationAAV,
)
from client.api_client import ApiClientError, PlatonAAVClient
from client.demo_data import load_demo_dataset
from client.services import AAVService, AttemptService, LearnerService


DEFAULT_API_URL = "http://127.0.0.1:8000"
NODE_WIDTH = 190
NODE_HEIGHT = 58


class PlatonAAVApp(tk.Tk):
    """Fenetre principale du client lourd PlatonAAV."""

    def __init__(self) -> None:
        """Initialise l'application Tkinter et ses services.

        Cree la fenetre principale, instancie le client HTTP, branche les
        services applicatifs, puis construit les onglets de l'interface.
        """
        super().__init__()
        self.title("PlatonAAV - Architecte du Savoir")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.client = PlatonAAVClient(DEFAULT_API_URL)
        self.aav_service = AAVService(self.client)
        self.learner_service = LearnerService(self.client)
        self.attempt_service = AttemptService(self.client)

        self.aavs: list[AAV] = []
        self.learners = []
        self.selected_aav_id: int | None = None
        self.graph_nodes: dict[int, tuple[int, int]] = {}

        self._configure_style()
        self._build_layout()
        self.after(150, self.refresh_all)

    def _configure_style(self) -> None:
        """Configure le theme et les styles Tkinter utilises par l'application."""
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=26)
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Status.TLabel", foreground="#155724")
        style.configure("Error.TLabel", foreground="#8a1f11")

    def _build_layout(self) -> None:
        """Construit le squelette principal de l'interface.

        Ajoute la barre d'URL API, le bouton de test, le bouton de chargement
        demo, les onglets fonctionnels et la barre de statut.
        """
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(10, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="URL API").grid(row=0, column=0, sticky="w")
        self.api_url_var = tk.StringVar(value=DEFAULT_API_URL)
        ttk.Entry(header, textvariable=self.api_url_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(header, text="Appliquer", command=self.apply_api_url).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(header, text="Tester", command=self.check_api).grid(
            row=0, column=3
        )
        ttk.Button(header, text="Charger demo", command=self.load_demo_data).grid(
            row=0, column=4, padx=(8, 0)
        )

        self.status_var = tk.StringVar(value="Pret.")
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            style="Status.TLabel",
            padding=(10, 0, 10, 6),
        )
        self.status_label.grid(row=2, column=0, sticky="ew")

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self._build_aav_tab()
        self._build_learner_tab()
        self._build_attempt_tab()
        self._build_graph_tab()
        self._build_demo_tab()

    def _build_aav_tab(self) -> None:
        """Construit l'onglet de consultation et d'edition des AAV."""
        tab = ttk.Frame(self.notebook, padding=8)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        self.notebook.add(tab, text="AAV")

        filters = ttk.Frame(tab)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        filters.columnconfigure(1, weight=1)

        ttk.Label(filters, text="Discipline").grid(row=0, column=0, sticky="w")
        self.aav_filter_discipline = tk.StringVar()
        ttk.Entry(filters, textvariable=self.aav_filter_discipline, width=24).grid(
            row=0, column=1, sticky="w", padx=(6, 16)
        )

        ttk.Label(filters, text="Type").grid(row=0, column=2, sticky="w")
        self.aav_filter_type = tk.StringVar()
        ttk.Combobox(
            filters,
            textvariable=self.aav_filter_type,
            values=["", *[item.value for item in TypeAAV]],
            state="readonly",
            width=24,
        ).grid(row=0, column=3, sticky="w", padx=(6, 16))

        ttk.Button(filters, text="Rafraichir", command=self.refresh_aavs).grid(
            row=0, column=4, sticky="e"
        )

        pane = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        pane.grid(row=1, column=0, sticky="nsew")

        left = ttk.Frame(pane)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        pane.add(left, weight=2)

        columns = ("id", "nom", "discipline", "type")
        self.aav_tree = ttk.Treeview(
            left,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        for column, label, width in (
            ("id", "ID", 70),
            ("nom", "Nom", 260),
            ("discipline", "Discipline", 130),
            ("type", "Type", 150),
        ):
            self.aav_tree.heading(column, text=label)
            self.aav_tree.column(column, width=width, anchor="w")
        self.aav_tree.grid(row=0, column=0, sticky="nsew")
        self.aav_tree.bind("<<TreeviewSelect>>", self.on_aav_selected)

        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.aav_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.aav_tree.configure(yscrollcommand=yscroll.set)

        right = ttk.Frame(pane, padding=(12, 0, 0, 0))
        right.columnconfigure(1, weight=1)
        pane.add(right, weight=3)
        self._build_aav_form(right)

    def _build_aav_form(self, parent: ttk.Frame) -> None:
        """Construit le formulaire de creation et modification d'un AAV.

        Args:
            parent: Conteneur Tkinter dans lequel inserer le formulaire.
        """
        ttk.Label(parent, text="Formulaire AAV", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.aav_id_var = tk.StringVar()
        self.aav_nom_var = tk.StringVar()
        self.aav_libelle_var = tk.StringVar()
        self.aav_discipline_var = tk.StringVar()
        self.aav_enseignement_var = tk.StringVar()
        self.aav_type_var = tk.StringVar(value=TypeAAV.ATOMIQUE.value)
        self.aav_evaluation_var = tk.StringVar(value=TypeEvaluationAAV.HUMAINE.value)
        self.aav_prerequis_var = tk.StringVar()
        self.aav_external_var = tk.StringVar()
        self.aav_interdisc_var = tk.StringVar()
        self.aav_children_var = tk.StringVar()
        self.aav_exercises_var = tk.StringVar()
        self.aav_prompts_var = tk.StringVar()
        self.aav_threshold_var = tk.StringVar(value="0.7")
        self.aav_mastery_var = tk.StringVar(value="1.0")
        self.aav_success_count_var = tk.StringVar(value="1")
        self.relation_aav_var = tk.StringVar()
        self.child_weight_var = tk.StringVar(value="1.0")

        row = 1
        row = self._entry_row(parent, row, "ID", self.aav_id_var)
        row = self._entry_row(parent, row, "Nom", self.aav_nom_var)
        row = self._entry_row(parent, row, "Libelle", self.aav_libelle_var)
        row = self._entry_row(parent, row, "Discipline", self.aav_discipline_var)
        row = self._entry_row(parent, row, "Enseignement", self.aav_enseignement_var)

        ttk.Label(parent, text="Type").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Combobox(
            parent,
            textvariable=self.aav_type_var,
            values=[item.value for item in TypeAAV],
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Label(parent, text="Evaluation").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Combobox(
            parent,
            textvariable=self.aav_evaluation_var,
            values=[item.value for item in TypeEvaluationAAV],
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        ttk.Label(parent, text="AAV lie").grid(row=row, column=0, sticky="w", pady=3)
        self.relation_aav_combo = ttk.Combobox(
            parent,
            textvariable=self.relation_aav_var,
            state="readonly",
        )
        self.relation_aav_combo.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        relation_actions = ttk.Frame(parent)
        relation_actions.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        for index in range(3):
            relation_actions.columnconfigure(index, weight=1)
        ttk.Button(
            relation_actions,
            text="Ajouter comme prerequis",
            command=self.add_selected_prerequisite,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Entry(relation_actions, textvariable=self.child_weight_var, width=8).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=6,
        )
        ttk.Button(
            relation_actions,
            text="Ajouter comme enfant",
            command=self.add_selected_child,
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))
        row += 1

        row = self._entry_row(parent, row, "Prerequis IDs", self.aav_prerequis_var)
        row = self._entry_row(parent, row, "Prerequis externes", self.aav_external_var)
        row = self._entry_row(parent, row, "Code interdisc.", self.aav_interdisc_var)
        row = self._entry_row(parent, row, "Enfants ponderees", self.aav_children_var)
        row = self._entry_row(parent, row, "Exercices IDs", self.aav_exercises_var)
        row = self._entry_row(parent, row, "Prompts IDs", self.aav_prompts_var)
        row = self._entry_row(parent, row, "Seuil succes", self.aav_threshold_var)
        row = self._entry_row(parent, row, "Maitrise requise", self.aav_mastery_var)
        row = self._entry_row(
            parent,
            row,
            "Succes consecutifs",
            self.aav_success_count_var,
        )

        ttk.Label(parent, text="Description").grid(row=row, column=0, sticky="nw", pady=3)
        self.aav_description_text = tk.Text(parent, height=7, wrap="word")
        self.aav_description_text.grid(row=row, column=1, sticky="nsew", pady=3)
        parent.rowconfigure(row, weight=1)
        row += 1

        help_label = ttk.Label(
            parent,
            text="Listes: 1,2,3 | Enfants: 1:0.5, 2:0.5 ou JSON [[1,0.5]]",
        )
        help_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 8))
        row += 1

        actions = ttk.Frame(parent)
        actions.grid(row=row, column=0, columnspan=2, sticky="ew")
        for index in range(4):
            actions.columnconfigure(index, weight=1)
        ttk.Button(actions, text="Nouveau", command=self.clear_aav_form).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(actions, text="Creer", command=self.create_aav).grid(
            row=0, column=1, sticky="ew", padx=6
        )
        ttk.Button(actions, text="Modifier", command=self.update_aav).grid(
            row=0, column=2, sticky="ew", padx=6
        )
        ttk.Button(actions, text="Supprimer", command=self.delete_aav).grid(
            row=0, column=3, sticky="ew", padx=(6, 0)
        )

    def _build_learner_tab(self) -> None:
        """Construit l'onglet de creation et suivi des apprenants."""
        tab = ttk.Frame(self.notebook, padding=8)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(3, weight=1)
        self.notebook.add(tab, text="Apprenants")

        create_box = ttk.LabelFrame(tab, text="Creation rapide", padding=8)
        create_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        create_box.columnconfigure(1, weight=1)
        create_box.columnconfigure(3, weight=1)

        self.learner_id_var = tk.StringVar()
        self.learner_name_var = tk.StringVar()
        self.learner_email_var = tk.StringVar()

        ttk.Label(create_box, text="ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(create_box, textvariable=self.learner_id_var, width=10).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 14),
        )
        ttk.Label(create_box, text="Nom").grid(row=0, column=2, sticky="w")
        ttk.Entry(create_box, textvariable=self.learner_name_var).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(6, 14),
        )
        ttk.Label(create_box, text="Email").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(create_box, textvariable=self.learner_email_var).grid(
            row=1,
            column=1,
            columnspan=3,
            sticky="ew",
            padx=(6, 14),
            pady=(6, 0),
        )
        ttk.Button(create_box, text="Creer apprenant", command=self.create_learner).grid(
            row=0,
            column=4,
            rowspan=2,
            sticky="nsew",
        )

        top = ttk.Frame(tab)
        top.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Apprenant").grid(row=0, column=0, sticky="w")
        self.learner_choice_var = tk.StringVar()
        self.learner_combo = ttk.Combobox(
            top,
            textvariable=self.learner_choice_var,
            state="readonly",
        )
        self.learner_combo.grid(row=0, column=1, sticky="ew", padx=8)
        self.learner_combo.bind("<<ComboboxSelected>>", self.refresh_selected_learner)

        ttk.Button(top, text="Rafraichir", command=self.refresh_learners).grid(
            row=0, column=2
        )

        self.summary_var = tk.StringVar(value="Aucun apprenant selectionne.")
        ttk.Label(tab, textvariable=self.summary_var).grid(
            row=2, column=0, sticky="ew", pady=(0, 8)
        )

        columns = ("id", "aav", "niveau", "maitrise", "tentatives")
        self.status_tree = ttk.Treeview(tab, columns=columns, show="headings")
        for column, label, width in (
            ("id", "Statut", 80),
            ("aav", "AAV cible", 100),
            ("niveau", "Niveau", 100),
            ("maitrise", "Maitrise", 100),
            ("tentatives", "Tentatives", 240),
        ):
            self.status_tree.heading(column, text=label)
            self.status_tree.column(column, width=width, anchor="w")
        self.status_tree.grid(row=3, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.status_tree.yview)
        yscroll.grid(row=3, column=1, sticky="ns")
        self.status_tree.configure(yscrollcommand=yscroll.set)

    def _build_attempt_tab(self) -> None:
        """Construit l'onglet de simulation d'une tentative."""
        tab = ttk.Frame(self.notebook, padding=8)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(7, weight=1)
        self.notebook.add(tab, text="Simulation")

        ttk.Label(tab, text="Simulation d'une tentative", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        self.attempt_learner_var = tk.StringVar()
        self.attempt_aav_var = tk.StringVar()
        self.attempt_exercise_var = tk.StringVar(value="1001")
        self.attempt_score_var = tk.StringVar(value="0.8")
        self.attempt_valid_var = tk.BooleanVar(value=True)
        self.attempt_time_var = tk.StringVar()

        ttk.Label(tab, text="Apprenant").grid(row=1, column=0, sticky="w", pady=4)
        self.attempt_learner_combo = ttk.Combobox(
            tab,
            textvariable=self.attempt_learner_var,
            state="readonly",
        )
        self.attempt_learner_combo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(tab, text="AAV").grid(row=2, column=0, sticky="w", pady=4)
        self.attempt_aav_combo = ttk.Combobox(
            tab,
            textvariable=self.attempt_aav_var,
            state="readonly",
        )
        self.attempt_aav_combo.grid(row=2, column=1, sticky="ew", pady=4)

        row = 3
        row = self._entry_row(tab, row, "Exercice/evenement", self.attempt_exercise_var)
        row = self._entry_row(tab, row, "Score 0..1", self.attempt_score_var)
        row = self._entry_row(tab, row, "Temps secondes", self.attempt_time_var)

        ttk.Checkbutton(
            tab,
            text="Tentative valide",
            variable=self.attempt_valid_var,
        ).grid(row=row, column=1, sticky="w", pady=4)
        row += 1

        ttk.Button(
            tab,
            text="Creer et traiter la tentative",
            command=self.create_and_process_attempt,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 10))
        row += 1

        self.attempt_result_text = tk.Text(tab, height=12, wrap="word")
        self.attempt_result_text.grid(row=row, column=0, columnspan=2, sticky="nsew")

    def _build_graph_tab(self) -> None:
        """Construit l'onglet affichant le graphe des relations entre AAV."""
        tab = ttk.Frame(self.notebook, padding=8)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        self.notebook.add(tab, text="Graphe")

        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(1, weight=1)
        ttk.Button(top, text="Rafraichir graphe", command=self.draw_graph).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            top,
            text="Gris: prerequis. Vert: enfant vers AAV composite.",
            style="Hint.TLabel",
        ).grid(row=0, column=1, sticky="w", padx=12)

        canvas_frame = ttk.Frame(tab)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.graph_canvas = tk.Canvas(canvas_frame, background="white")
        self.graph_canvas.grid(row=0, column=0, sticky="nsew")
        xscroll = ttk.Scrollbar(
            canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.graph_canvas.xview,
        )
        yscroll = ttk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
            command=self.graph_canvas.yview,
        )
        xscroll.grid(row=1, column=0, sticky="ew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.graph_canvas.configure(
            xscrollcommand=xscroll.set,
            yscrollcommand=yscroll.set,
        )

    def _build_demo_tab(self) -> None:
        """Construit l'onglet d'aide au scenario de soutenance."""
        tab = ttk.Frame(self.notebook, padding=12)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        self.notebook.add(tab, text="Demo")

        ttk.Label(tab, text="Scenario de soutenance", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 8),
        )
        text = tk.Text(tab, height=18, wrap="word")
        text.grid(row=1, column=0, sticky="nsew")
        text.insert(
            "1.0",
            "\n".join(
                [
                    "1. Lancer l'API FastAPI.",
                    "2. Lancer ce client Tkinter.",
                    "3. Cliquer sur Charger demo si la base est vide.",
                    "4. Onglet AAV: montrer la liste, les filtres, puis ouvrir un AAV.",
                    "5. Montrer les prerequis et les enfants ponderees.",
                    "6. Onglet Graphe: afficher le reseau pedagogique.",
                    "7. Onglet Apprenants: creer ou selectionner un apprenant.",
                    "8. Onglet Simulation: creer une tentative.",
                    "9. Retourner dans Apprenants pour montrer la progression.",
                    "",
                    "Flux technique:",
                    "Tkinter -> services client -> requests -> FastAPI -> SQLite -> JSON -> Tkinter.",
                ]
            ),
        )
        text.configure(state="disabled")
        ttk.Button(
            tab,
            text="Charger les donnees de demonstration",
            command=self.load_demo_data,
        ).grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _entry_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> int:
        """Ajoute une ligne label + champ texte dans un formulaire.

        Args:
            parent: Conteneur Tkinter cible.
            row: Index de ligne ou inserer les widgets.
            label: Libelle affiche a gauche.
            variable: Variable Tkinter liee au champ texte.

        Returns:
            Index de la prochaine ligne disponible.
        """
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", pady=3
        )
        return row + 1

    def apply_api_url(self) -> None:
        """Applique l'URL API saisie par l'utilisateur et recharge les donnees."""
        self.client.set_base_url(self.api_url_var.get())
        self.set_status(f"API cible: {self.client.base_url}")
        self.refresh_all()

    def check_api(self) -> None:
        """Verifie que l'API cible repond sur l'endpoint `/health`."""
        try:
            data = self.client.get("/health")
        except ApiClientError as exc:
            self.show_error(exc.message)
            return
        self.set_status(f"Connexion OK: {data}")

    def load_demo_data(self) -> None:
        """Charge le jeu de donnees demo via les services client.

        Les donnees sont envoyees a l'API avec les memes chemins que l'interface
        utilisateur. Cela evite d'ecrire directement dans SQLite depuis Tkinter.
        """
        try:
            self.client.get("/health")
            result = load_demo_dataset(
                self.aav_service,
                self.learner_service,
                self.attempt_service,
            )
        except (ApiClientError, ValidationError, ValueError) as exc:
            self.show_error(str(exc))
            return

        self.refresh_all()
        self.set_status(
            f"Demo chargee: {result.aavs} AAV, "
            f"{result.learners_created} apprenants crees, "
            f"{result.attempts_created} tentatives ajoutees."
        )
        messagebox.showinfo("Demo", "Donnees de demonstration chargees.")

    def refresh_all(self) -> None:
        """Recharge les AAV et les apprenants depuis l'API."""
        self.refresh_aavs()
        self.refresh_learners()

    def refresh_aavs(self) -> None:
        """Recharge la liste des AAV selon les filtres actifs."""
        try:
            self.aavs = self.aav_service.list_aavs(
                discipline=self.aav_filter_discipline.get().strip() or None,
                type_aav=self.aav_filter_type.get().strip() or None,
            )
        except ApiClientError as exc:
            self.show_error(exc.message)
            return

        for item in self.aav_tree.get_children():
            self.aav_tree.delete(item)
        for aav in self.aavs:
            self.aav_tree.insert(
                "",
                tk.END,
                iid=str(aav.id_aav),
                values=(aav.id_aav, aav.nom, aav.discipline, aav.type_aav.value),
            )

        self._refresh_aav_combobox()
        self.draw_graph()
        self.set_status(f"{len(self.aavs)} AAV charges.")

    def refresh_learners(self) -> None:
        """Recharge la liste des apprenants dans les menus deroulants."""
        try:
            self.learners = self.learner_service.list_learners()
        except ApiClientError as exc:
            self.show_error(exc.message)
            return

        labels = [self._learner_label(learner) for learner in self.learners]
        self.learner_combo.configure(values=labels)
        self.attempt_learner_combo.configure(values=labels)
        if labels and not self.learner_choice_var.get():
            self.learner_choice_var.set(labels[0])
            self.attempt_learner_var.set(labels[0])
            self.refresh_selected_learner()

    def create_learner(self) -> None:
        """Cree un apprenant a partir du formulaire de l'onglet Apprenants."""
        try:
            payload = LearnerCreate(
                id_apprenant=int(self.learner_id_var.get()),
                nom_utilisateur=self.learner_name_var.get().strip(),
                email=self.learner_email_var.get().strip(),
            )
            learner = self.learner_service.create_learner(payload)
        except (ApiClientError, ValidationError, ValueError) as exc:
            self.show_error(str(exc))
            return

        label = self._learner_label(learner)
        self.learner_choice_var.set(label)
        self.attempt_learner_var.set(label)
        self.learner_id_var.set("")
        self.learner_name_var.set("")
        self.learner_email_var.set("")
        self.refresh_learners()
        self.set_status(f"Apprenant {learner.id_apprenant} cree.")

    def refresh_selected_learner(self, _event: object | None = None) -> None:
        """Recharge les statuts de l'apprenant selectionne.

        Args:
            _event: Evenement Tkinter optionnel emis par la combobox.
        """
        learner_id = self._id_from_label(self.learner_choice_var.get())
        if learner_id is None:
            return

        try:
            statuses = self.learner_service.get_learning_status(learner_id)
            summary = self.learner_service.get_summary(learner_id)
        except ApiClientError as exc:
            self.show_error(exc.message)
            return

        self.summary_var.set(
            "Total: {total} | Maitrises: {maitrise} | En cours: {en_cours} | "
            "Non commence: {non_commence} | Taux: {taux}%".format(
                total=summary.total,
                maitrise=summary.maitrise,
                en_cours=summary.en_cours,
                non_commence=summary.non_commence,
                taux=summary.taux_maitrise_global,
            )
        )

        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
        for status in statuses:
            self.status_tree.insert(
                "",
                tk.END,
                iid=str(status.id),
                values=(
                    status.id,
                    status.id_aav_cible,
                    f"{status.niveau_maitrise:.2f}",
                    "oui" if status.est_maitrise else "non",
                    ", ".join(str(item) for item in status.historique_tentatives_ids),
                ),
            )

    def on_aav_selected(self, _event: object | None = None) -> None:
        """Remplit le formulaire lorsqu'un AAV est selectionne dans le tableau.

        Args:
            _event: Evenement Tkinter optionnel emis par le tableau.
        """
        selection = self.aav_tree.selection()
        if not selection:
            return
        self.selected_aav_id = int(selection[0])
        aav = next((item for item in self.aavs if item.id_aav == self.selected_aav_id), None)
        if aav is not None:
            self.fill_aav_form(aav)

    def fill_aav_form(self, aav: AAV) -> None:
        """Injecte les donnees d'un AAV dans le formulaire d'edition.

        Args:
            aav: AAV selectionne dans la liste ou dans le graphe.
        """
        self.aav_id_var.set(str(aav.id_aav))
        self.aav_nom_var.set(aav.nom)
        self.aav_libelle_var.set(aav.libelle_integration)
        self.aav_discipline_var.set(aav.discipline)
        self.aav_enseignement_var.set(aav.enseignement)
        self.aav_type_var.set(aav.type_aav.value)
        self.aav_evaluation_var.set(aav.type_evaluation.value)
        self.aav_prerequis_var.set(self._list_to_text(aav.prerequis_ids))
        self.aav_external_var.set(self._list_to_text(aav.prerequis_externes_codes))
        self.aav_interdisc_var.set(aav.code_prerequis_interdisciplinaire or "")
        self.aav_children_var.set(
            ", ".join(f"{child}:{weight}" for child, weight in aav.aav_enfant_ponderation)
        )
        self.aav_exercises_var.set(self._list_to_text(aav.ids_exercices))
        self.aav_prompts_var.set(self._list_to_text(aav.prompts_fabrication_ids))
        self.aav_threshold_var.set(str(aav.regles_progression.seuil_succes))
        self.aav_mastery_var.set(str(aav.regles_progression.maitrise_requise))
        self.aav_success_count_var.set(str(aav.regles_progression.nombre_succes_consecutifs))
        self.aav_description_text.delete("1.0", tk.END)
        self.aav_description_text.insert("1.0", aav.description_markdown)

    def clear_aav_form(self) -> None:
        """Reinitialise le formulaire AAV pour une nouvelle saisie."""
        self.selected_aav_id = None
        for variable in (
            self.aav_id_var,
            self.aav_nom_var,
            self.aav_libelle_var,
            self.aav_discipline_var,
            self.aav_enseignement_var,
            self.aav_prerequis_var,
            self.aav_external_var,
            self.aav_interdisc_var,
            self.aav_children_var,
            self.aav_exercises_var,
            self.aav_prompts_var,
        ):
            variable.set("")
        self.aav_type_var.set(TypeAAV.ATOMIQUE.value)
        self.aav_evaluation_var.set(TypeEvaluationAAV.HUMAINE.value)
        self.aav_threshold_var.set("0.7")
        self.aav_mastery_var.set("1.0")
        self.aav_success_count_var.set("1")
        self.child_weight_var.set("1.0")
        self.aav_description_text.delete("1.0", tk.END)
        self.aav_tree.selection_remove(self.aav_tree.selection())

    def add_selected_prerequisite(self) -> None:
        """Ajoute l'AAV choisi comme prerequis de l'AAV courant."""
        relation_id = self._id_from_label(self.relation_aav_var.get())
        current_id = self._current_aav_id()
        if relation_id is None:
            self.show_error("Choisissez un AAV existant.")
            return
        if current_id == relation_id:
            self.show_error("Un AAV ne peut pas etre son propre prerequis.")
            return

        values = self._parse_int_list(self.aav_prerequis_var.get())
        if relation_id not in values:
            values.append(relation_id)
        self.aav_prerequis_var.set(self._list_to_text(values))

    def add_selected_child(self) -> None:
        """Ajoute l'AAV choisi comme enfant pondere de l'AAV courant."""
        relation_id = self._id_from_label(self.relation_aav_var.get())
        current_id = self._current_aav_id()
        if relation_id is None:
            self.show_error("Choisissez un AAV existant.")
            return
        if current_id == relation_id:
            self.show_error("Un AAV ne peut pas etre son propre enfant.")
            return
        try:
            weight = float(self.child_weight_var.get().replace(",", "."))
        except ValueError:
            self.show_error("Le poids enfant doit etre un nombre.")
            return

        children = [
            (child, existing_weight)
            for child, existing_weight in self._parse_weighted_children(
                self.aav_children_var.get()
            )
            if child != relation_id
        ]
        children.append((relation_id, weight))
        self.aav_children_var.set(
            ", ".join(f"{child}:{child_weight}" for child, child_weight in children)
        )
        self.aav_type_var.set(TypeAAV.COMPOSITE.value)

    def create_aav(self) -> None:
        """Cree un AAV depuis le formulaire et recharge la liste."""
        try:
            payload = self._build_aav_create_payload()
            created = self.aav_service.create_aav(payload)
        except (ApiClientError, ValidationError, ValueError) as exc:
            self.show_error(str(exc))
            return

        self.set_status(f"AAV {created.id_aav} cree.")
        self.refresh_aavs()
        self._select_aav(created.id_aav)

    def update_aav(self) -> None:
        """Met a jour l'AAV selectionne depuis le formulaire."""
        id_aav = self._current_aav_id()
        if id_aav is None:
            self.show_error("Selectionnez un AAV a modifier.")
            return

        try:
            payload = self._build_aav_update_payload()
            updated = self.aav_service.update_aav(id_aav, payload)
        except (ApiClientError, ValidationError, ValueError) as exc:
            self.show_error(str(exc))
            return

        self.set_status(f"AAV {updated.id_aav} modifie.")
        self.refresh_aavs()
        self._select_aav(updated.id_aav)

    def delete_aav(self) -> None:
        """Supprime logiquement l'AAV selectionne apres confirmation."""
        id_aav = self._current_aav_id()
        if id_aav is None:
            self.show_error("Selectionnez un AAV a supprimer.")
            return
        if not messagebox.askyesno("Confirmer", f"Supprimer l'AAV {id_aav} ?"):
            return

        try:
            self.aav_service.delete_aav(id_aav)
        except ApiClientError as exc:
            self.show_error(exc.message)
            return

        self.set_status(f"AAV {id_aav} supprime.")
        self.clear_aav_form()
        self.refresh_aavs()

    def create_and_process_attempt(self) -> None:
        """Cree une tentative puis declenche son traitement de maitrise."""
        try:
            learner_id = self._id_from_label(self.attempt_learner_var.get())
            aav_id = self._id_from_label(self.attempt_aav_var.get())
            if learner_id is None or aav_id is None:
                raise ValueError("Choisissez un apprenant et un AAV.")

            time_raw = self.attempt_time_var.get().strip()
            payload = TentativeCreate(
                id_exercice_ou_evenement=int(self.attempt_exercise_var.get()),
                id_apprenant=learner_id,
                id_aav_cible=aav_id,
                score_obtenu=float(self.attempt_score_var.get().replace(",", ".")),
                est_valide=self.attempt_valid_var.get(),
                temps_resolution_secondes=int(time_raw) if time_raw else None,
                metadata={"source": "client_tkinter"},
            )
            attempt = self.attempt_service.create_attempt(payload)
            process = self.attempt_service.process_attempt(attempt.id)
        except (ApiClientError, ValidationError, ValueError) as exc:
            self.show_error(str(exc))
            return

        self.attempt_result_text.delete("1.0", tk.END)
        self.attempt_result_text.insert(
            "1.0",
            "\n".join(
                [
                    f"Tentative creee: {attempt.id}",
                    f"Apprenant: {process.id_apprenant}",
                    f"AAV: {process.id_aav_cible}",
                    f"Ancien niveau: {process.ancien_niveau:.2f}",
                    f"Nouveau niveau: {process.nouveau_niveau:.2f}",
                    f"Maitrise: {'oui' if process.est_maitrise else 'non'}",
                    f"Message: {process.message}",
                ]
            ),
        )
        self.set_status(f"Tentative {attempt.id} traitee.")
        self.refresh_selected_learner()

    def draw_graph(self) -> None:
        """Dessine le graphe des prerequis et des AAV composites sur le Canvas."""
        if not hasattr(self, "graph_canvas"):
            return

        canvas = self.graph_canvas
        canvas.delete("all")
        self.graph_nodes = {}

        if not self.aavs:
            canvas.create_text(
                30,
                30,
                text="Aucun AAV a afficher.",
                anchor="nw",
                fill="#555",
            )
            return

        width = max(canvas.winfo_width(), 900)
        cols = max(1, width // 260)
        margin_x = 45
        margin_y = 45
        gap_x = 250
        gap_y = 130

        sorted_aavs = sorted(self.aavs, key=lambda item: item.id_aav)
        for index, aav in enumerate(sorted_aavs):
            col = index % cols
            row = index // cols
            x = margin_x + col * gap_x + NODE_WIDTH // 2
            y = margin_y + row * gap_y + NODE_HEIGHT // 2
            self.graph_nodes[aav.id_aav] = (x, y)

        aav_ids = set(self.graph_nodes)
        for aav in sorted_aavs:
            for prereq_id in aav.prerequis_ids:
                if prereq_id in aav_ids:
                    self._draw_edge(prereq_id, aav.id_aav, "#777", dash=(4, 2))

            for child_id, _weight in aav.aav_enfant_ponderation:
                if child_id in aav_ids:
                    self._draw_edge(child_id, aav.id_aav, "#2f7d32", dash=None)

        for aav in sorted_aavs:
            self._draw_node(aav)

        rows = (len(sorted_aavs) + cols - 1) // cols
        canvas.configure(
            scrollregion=(0, 0, max(width, cols * gap_x + 80), rows * gap_y + 100)
        )

    def _draw_edge(
        self,
        source_id: int,
        target_id: int,
        color: str,
        dash: tuple[int, int] | None,
    ) -> None:
        """Dessine une relation orientee entre deux AAV.

        Args:
            source_id: Identifiant du noeud source.
            target_id: Identifiant du noeud cible.
            color: Couleur du trait.
            dash: Motif de pointilles, ou `None` pour un trait plein.
        """
        x1, y1 = self.graph_nodes[source_id]
        x2, y2 = self.graph_nodes[target_id]
        self.graph_canvas.create_line(
            x1,
            y1,
            x2,
            y2,
            arrow=tk.LAST,
            fill=color,
            width=2,
            dash=dash,
        )

    def _draw_node(self, aav: AAV) -> None:
        """Dessine un noeud AAV cliquable dans le graphe.

        Args:
            aav: AAV a representer dans le canvas.
        """
        x, y = self.graph_nodes[aav.id_aav]
        color = "#eef5ff" if aav.type_aav == TypeAAV.ATOMIQUE else "#edf8ee"
        outline = "#376996" if aav.type_aav == TypeAAV.ATOMIQUE else "#2f7d32"
        tag = f"node_{aav.id_aav}"
        x1 = x - NODE_WIDTH // 2
        y1 = y - NODE_HEIGHT // 2
        x2 = x + NODE_WIDTH // 2
        y2 = y + NODE_HEIGHT // 2

        self.graph_canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline=outline,
            width=2,
            tags=(tag,),
        )
        self.graph_canvas.create_text(
            x,
            y - 10,
            text=f"{aav.id_aav} - {aav.nom}",
            width=NODE_WIDTH - 14,
            font=("Segoe UI", 9, "bold"),
            tags=(tag,),
        )
        self.graph_canvas.create_text(
            x,
            y + 14,
            text=aav.discipline,
            width=NODE_WIDTH - 14,
            fill="#555",
            tags=(tag,),
        )
        self.graph_canvas.tag_bind(
            tag,
            "<Button-1>",
            lambda _event, id_aav=aav.id_aav: self.select_aav_from_graph(id_aav),
        )

    def select_aav_from_graph(self, id_aav: int) -> None:
        """Selectionne dans le formulaire l'AAV clique dans le graphe.

        Args:
            id_aav: Identifiant de l'AAV clique.
        """
        self.notebook.select(0)
        self._select_aav(id_aav)
        aav = next((item for item in self.aavs if item.id_aav == id_aav), None)
        if aav is not None:
            self.fill_aav_form(aav)

    def _build_aav_create_payload(self) -> AAVCreate:
        """Construit le modele Pydantic utilise pour creer un AAV.

        Returns:
            Instance `AAVCreate` validee a partir des champs du formulaire.
        """
        return AAVCreate(
            id_aav=int(self.aav_id_var.get()),
            nom=self.aav_nom_var.get().strip(),
            libelle_integration=self.aav_libelle_var.get().strip(),
            discipline=self.aav_discipline_var.get().strip(),
            enseignement=self.aav_enseignement_var.get().strip(),
            type_aav=TypeAAV(self.aav_type_var.get()),
            description_markdown=self._description(),
            prerequis_ids=self._parse_int_list(self.aav_prerequis_var.get()),
            prerequis_externes_codes=self._parse_str_list(self.aav_external_var.get()),
            code_prerequis_interdisciplinaire=self.aav_interdisc_var.get().strip() or None,
            aav_enfant_ponderation=self._parse_weighted_children(self.aav_children_var.get()),
            ids_exercices=self._parse_int_list(self.aav_exercises_var.get()),
            prompts_fabrication_ids=self._parse_int_list(self.aav_prompts_var.get()),
            type_evaluation=TypeEvaluationAAV(self.aav_evaluation_var.get()),
            regles_progression=self._progression_rules(),
        )

    def _build_aav_update_payload(self) -> AAVUpdate:
        """Construit le modele Pydantic utilise pour modifier un AAV.

        Returns:
            Instance `AAVUpdate` validee a partir des champs du formulaire.
        """
        return AAVUpdate(
            nom=self.aav_nom_var.get().strip(),
            libelle_integration=self.aav_libelle_var.get().strip(),
            discipline=self.aav_discipline_var.get().strip(),
            enseignement=self.aav_enseignement_var.get().strip(),
            type_aav=TypeAAV(self.aav_type_var.get()),
            type_evaluation=TypeEvaluationAAV(self.aav_evaluation_var.get()),
            description_markdown=self._description(),
            prerequis_ids=self._parse_int_list(self.aav_prerequis_var.get()),
            prerequis_externes_codes=self._parse_str_list(self.aav_external_var.get()),
            code_prerequis_interdisciplinaire=self.aav_interdisc_var.get().strip() or None,
            aav_enfant_ponderation=self._parse_weighted_children(self.aav_children_var.get()),
            ids_exercices=self._parse_int_list(self.aav_exercises_var.get()),
            prompts_fabrication_ids=self._parse_int_list(self.aav_prompts_var.get()),
            regles_progression=self._progression_rules(),
        )

    def _progression_rules(self) -> RegleProgression:
        """Construit les regles de progression depuis le formulaire.

        Returns:
            Modele `RegleProgression` valide par Pydantic.
        """
        return RegleProgression(
            seuil_succes=float(self.aav_threshold_var.get().replace(",", ".")),
            maitrise_requise=float(self.aav_mastery_var.get().replace(",", ".")),
            nombre_succes_consecutifs=int(self.aav_success_count_var.get()),
        )

    def _description(self) -> str:
        """Retourne la description markdown saisie dans la zone de texte."""
        return self.aav_description_text.get("1.0", tk.END).strip()

    def _current_aav_id(self) -> int | None:
        """Determine l'identifiant de l'AAV actuellement selectionne.

        Returns:
            Identifiant selectionne, identifiant saisi, ou `None`.
        """
        if self.selected_aav_id is not None:
            return self.selected_aav_id
        raw = self.aav_id_var.get().strip()
        return int(raw) if raw.isdigit() else None

    def _select_aav(self, id_aav: int) -> None:
        """Selectionne visuellement un AAV dans le tableau.

        Args:
            id_aav: Identifiant de l'AAV a selectionner.
        """
        item_id = str(id_aav)
        if self.aav_tree.exists(item_id):
            self.aav_tree.selection_set(item_id)
            self.aav_tree.see(item_id)
            self.selected_aav_id = id_aav

    def _refresh_aav_combobox(self) -> None:
        """Recharge les menus deroulants qui listent les AAV disponibles."""
        labels = [self._aav_label(aav) for aav in self.aavs]
        self.attempt_aav_combo.configure(values=labels)
        if hasattr(self, "relation_aav_combo"):
            self.relation_aav_combo.configure(values=labels)
        if labels and not self.attempt_aav_var.get():
            self.attempt_aav_var.set(labels[0])

    def set_status(self, message: str) -> None:
        """Affiche un message de statut non bloquant.

        Args:
            message: Texte a afficher en bas de la fenetre.
        """
        self.status_label.configure(style="Status.TLabel")
        self.status_var.set(message)

    def show_error(self, message: str) -> None:
        """Affiche une erreur dans la barre de statut et dans une popup.

        Args:
            message: Message d'erreur lisible par l'utilisateur.
        """
        self.status_label.configure(style="Error.TLabel")
        self.status_var.set(message)
        messagebox.showerror("Erreur", message)

    @staticmethod
    def _parse_int_list(value: str) -> list[int]:
        """Parse une liste d'entiers saisie sous forme texte.

        Args:
            value: Texte de type `1,2,3` ou `1;2;3`.

        Returns:
            Liste d'entiers.
        """
        return [int(item) for item in _split_csv(value)]

    @staticmethod
    def _parse_str_list(value: str) -> list[str]:
        """Parse une liste de chaines saisie sous forme texte.

        Args:
            value: Texte de type `A,B,C` ou `A;B;C`.

        Returns:
            Liste de chaines nettoyees.
        """
        return [str(item).strip() for item in _split_csv(value)]

    @staticmethod
    def _parse_weighted_children(value: str) -> list[tuple[int, float]]:
        """Parse les enfants ponderes d'un AAV composite.

        Args:
            value: Texte au format `1:0.5, 2:0.5` ou JSON `[[1, 0.5]]`.

        Returns:
            Liste de couples `(id_enfant, poids)`.

        Raises:
            ValueError: Si un item ne respecte pas le format attendu.
        """
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("["):
            parsed = json.loads(raw)
            return [(int(child), float(weight)) for child, weight in parsed]

        result = []
        for item in _split_csv(raw):
            if ":" in item:
                child, weight = item.split(":", 1)
            elif "=" in item:
                child, weight = item.split("=", 1)
            else:
                raise ValueError("Format enfant invalide. Exemple: 1:0.5, 2:0.5")
            result.append((int(child.strip()), float(weight.strip().replace(",", "."))))
        return result

    @staticmethod
    def _list_to_text(items: Iterable[object]) -> str:
        """Convertit une liste en texte lisible pour les champs du formulaire."""
        return ", ".join(str(item) for item in items)

    @staticmethod
    def _learner_label(learner) -> str:
        """Construit le libelle affiche dans les menus apprenants."""
        return f"{learner.id_apprenant} - {learner.nom_utilisateur}"

    @staticmethod
    def _aav_label(aav: AAV) -> str:
        """Construit le libelle affiche dans les menus AAV."""
        return f"{aav.id_aav} - {aav.nom}"

    @staticmethod
    def _id_from_label(label: str) -> int | None:
        """Extrait l'identifiant numerique d'un libelle de combobox.

        Args:
            label: Libelle de type `12 - Nom`.

        Returns:
            Identifiant extrait, ou `None` si le libelle est vide/invalide.
        """
        if not label:
            return None
        head = label.split(" - ", 1)[0].strip()
        return int(head) if head.isdigit() else None


def _split_csv(value: str) -> list[str]:
    """Decoupe une saisie texte en elements separes par virgule ou point-virgule.

    Args:
        value: Texte libre saisi dans un champ liste.

    Returns:
        Liste des elements non vides, sans espaces superflus.
    """
    normalized = value.replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def run() -> None:
    """Lance la boucle principale de l'application Tkinter."""
    app = PlatonAAVApp()
    app.mainloop()
