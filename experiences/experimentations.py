import os
import sys
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET

# Permet d'importer les modules du projet depuis le dossier parent
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from main import run_pipeline
from config import Config


class ExperimentManager:
    """
    Gestionnaire d'expériences pour tester différents réglages
    sans casser la configuration globale du projet.
    """

    def __init__(self, root_dir=None):
        self.root_dir = root_dir or PROJECT_ROOT
        self.output_dir = os.path.join(self.root_dir, "exp_results")
        os.makedirs(self.output_dir, exist_ok=True)
        self.results_summary = []

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _save_run(self, final_df, exp_name, params_str):
        """
        Sauvegarde le DataFrame final de l'expérience avec un nom explicite.
        """
        if final_df is None or final_df.empty:
            print(f"Aucun resultat a sauvegarder pour {exp_name}")
            return None

        filename = f"{exp_name.upper()}_{params_str.upper()}_{self._timestamp()}.csv"
        path = os.path.join(self.output_dir, filename)

        final_df.to_csv(path, index=False)
        print(f"Fichier d'experience enregistre : {path}")
        return path

    def _parse_graphml_metrics(self, graphml_text):
        """
        Extrait des metriques simples depuis une chaine GraphML :
        - nombre de noeuds
        - nombre d'aretes
        - densite
        - distribution des labels de polarite (un label par arete)
        """
        labels_dist = {
            "ami": 0,
            "plutot_ami": 0,
            "neutre": 0,
            "plutot_ennemi": 0,
            "ennemi": 0
        }

        if not isinstance(graphml_text, str) or not graphml_text.strip():
            return {
                "nodes": 0,
                "edges": 0,
                "density": 0.0,
                "labels_dist": labels_dist
            }

        try:
            root = ET.fromstring(graphml_text)
            ns = {"g": "http://graphml.graphdrawing.org/xmlns"}

            nodes = root.findall(".//g:node", ns)
            edges = root.findall(".//g:edge", ns)

            n = len(nodes)
            e = len(edges)
            # densite pour graphe non oriente (formule classique)
            density = (2 * e) / (n * (n - 1)) if n > 1 else 0.0

            # Parcours des aretes pour extraire le label de polarite
            for edge in edges:
                # On cherche parmi les elements data celui qui contient le label
                found = False
                for data in edge.findall("g:data", ns):
                    # Si le texte correspond a une des cles de label, on l'enregistre
                    if data.text in labels_dist:
                        labels_dist[data.text] += 1
                        found = True
                        break  # Une arete ne porte qu'un seul label de polarite
                # Si aucune donnee ne correspond, l'arete n'est pas comptabilisee
                # (on pourrait optionnellement compter comme "neutre" mais on prefere ne rien ajouter)

            return {
                "nodes": n,
                "edges": e,
                "density": density,
                "labels_dist": labels_dist
            }

        except Exception as exc:
            print(f"Parsing GraphML impossible : {exc}")
            return {
                "nodes": 0,
                "edges": 0,
                "density": 0.0,
                "labels_dist": labels_dist
            }

    def _calculate_metrics(self, final_df):
        """
        Calcule les metriques agregees sur le DataFrame final :
        - densite moyenne
        - nombre total d'aretes
        - distribution globale des polarites
        """
        labels_dist_total = {
            "ami": 0,
            "plutot_ami": 0,
            "neutre": 0,
            "plutot_ennemi": 0,
            "ennemi": 0
        }

        if final_df is None or final_df.empty:
            return 0.0, 0, labels_dist_total

        if "graphml" not in final_df.columns:
            print("Colonne 'graphml' absente du DataFrame.")
            return 0.0, 0, labels_dist_total

        densities = []
        total_edges = 0

        for _, row in final_df.iterrows():
            metrics = self._parse_graphml_metrics(row["graphml"])
            densities.append(metrics["density"])
            total_edges += metrics["edges"]

            for label, count in metrics["labels_dist"].items():
                labels_dist_total[label] += count

        avg_density = sum(densities) / len(densities) if densities else 0.0
        return avg_density, total_edges, labels_dist_total

    def _run_pipeline_with_overrides(self, overrides):
        """
        Applique temporairement des surcharges de configuration,
        execute le pipeline, puis restaure la configuration initiale.
        """
        original_values = {}

        try:
            for attr_name, new_value in overrides.items():
                original_values[attr_name] = getattr(Config, attr_name)
                setattr(Config, attr_name, new_value)

            final_df = run_pipeline()
            return final_df

        finally:
            for attr_name, old_value in original_values.items():
                setattr(Config, attr_name, old_value)

    def run_exp_a_window_size(self, test_values=None):
        """
        Experience A :
        Impact de la taille de la fenetre de cooccurrence.
        """
        print("\n--- Lancement Experience A : taille de fenetre ---")
        test_values = test_values or [20] # , 20, 25, 30, 50

        for ws in test_values:
            print(f"\n> Test WINDOW_SIZE = {ws}")

            final_df = self._run_pipeline_with_overrides({
                "WINDOW_SIZE": ws
            })

            if final_df is not None and not final_df.empty:
                density, edge_count, labels = self._calculate_metrics(final_df)

                self.results_summary.append({
                    "experiment": "ExpA_WindowSize",
                    "tested_param": "WINDOW_SIZE",
                    "tested_value": ws,
                    "avg_density": round(density, 6),
                    "total_edges": edge_count,
                    "ami": labels["ami"],
                    "plutot_ami": labels["plutot_ami"],
                    "neutre": labels["neutre"],
                    "plutot_ennemi": labels["plutot_ennemi"],
                    "ennemi": labels["ennemi"]
                })

                self._save_run(final_df, "EXP_A", f"window_{ws}")
            else:
                print("Aucun DataFrame valide renvoye par run_pipeline().")

    def run_exp_d_sensitivity(self, factors=None):
        """
        Experience D :
        Analyse de sensibilite des coefficients de polarite.
        """
        print("\n--- Lancement Experience D : sensibilite des coefficients ---")
        factors = factors or [0.5, 1.0, 2.0]

        base_params = {
            "POLARITY_BETA": Config.POLARITY_BETA,
            "POLARITY_DELTA": Config.POLARITY_DELTA,
            "POLARITY_EPSILON": Config.POLARITY_EPSILON
        }

        for param_name, base_value in base_params.items():
            for factor in factors:
                tested_value = base_value * factor
                print(f"\n> Test {param_name} = {tested_value} (facteur {factor})")

                final_df = self._run_pipeline_with_overrides({
                    param_name: tested_value
                })

                if final_df is not None and not final_df.empty:
                    density, edge_count, labels = self._calculate_metrics(final_df)

                    self.results_summary.append({
                        "experiment": "ExpD_PolaritySensitivity",
                        "tested_param": param_name,
                        "base_value": base_value,
                        "factor": factor,
                        "tested_value": tested_value,
                        "avg_density": round(density, 6),
                        "total_edges": edge_count,
                        "ami": labels["ami"],
                        "plutot_ami": labels["plutot_ami"],
                        "neutre": labels["neutre"],
                        "plutot_ennemi": labels["plutot_ennemi"],
                        "ennemi": labels["ennemi"]
                    })

                    short_name = param_name.replace("POLARITY_", "").lower()
                    self._save_run(final_df, "EXP_D", f"{short_name}_x{factor}")
                else:
                    print("Aucun DataFrame valide renvoye par run_pipeline().")

    def export_summary(self):
        """
        Exporte le resume global de toutes les experiences.
        """
        if not self.results_summary:
            print("Aucun resultat resume a exporter.")
            return None

        summary_df = pd.DataFrame(self.results_summary)
        summary_path = os.path.join(
            self.output_dir,
            f"RESUME_EXPERIENCES_GLOBAL_{self._timestamp()}.csv"
        )
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSynthese finale generee : {summary_path}")
        return summary_path


if __name__ == "__main__":
    manager = ExperimentManager()

    # Experience A
    manager.run_exp_a_window_size()

    # Experience D (decommentez pour lancer)
    # manager.run_exp_d_sensitivity()

    # Export global
    manager.export_summary()