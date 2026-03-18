def test_mastery_uses_professor_rules_for_aav1(client):
    # Bob (2) / AAV 1 a déjà 0.70, 0.80, 0.85
    # Avec une nouvelle tentative à 0.95, les 3 dernières sont >= 0.8
    # donc maîtrise attendue selon la DB du prof.
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 102,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.95,
            "est_valide": True,
            "temps_resolution_secondes": 60,
            "metadata": None,
        },
    )
    assert r.status_code == 201
    attempt_id = r.json()["id"]

    r2 = client.post(f"/attempts/{attempt_id}/process")
    assert r2.status_code == 200

    data = r2.json()
    assert data["est_maitrise"] is True
    assert data["nouveau_niveau"] == 1.0