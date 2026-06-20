def normalize_odds(odds_dict):
    """
    Konvertiert Quoten in normalisierte Wahrscheinlichkeiten.
    Buchmacher haben eine Marge, wodurch die Summe der impliziten Wahrscheinlichkeiten > 1 ist.
    Wir teilen durch die Summe, um echte Wahrscheinlichkeiten (Summe = 1.0) zu erhalten.
    """
    probabilities = {}
    sum_implied_probs = 0.0
    
    for result, odd in odds_dict.items():
        if odd <= 0:
            continue
        implied_prob = 1.0 / odd
        sum_implied_probs += implied_prob
        probabilities[result] = implied_prob
        
    # Normalisieren
    normalized_probs = {}
    for result, prob in probabilities.items():
        normalized_probs[result] = prob / sum_implied_probs
        
    return normalized_probs

def calculate_kicktipp_points(tip_home, tip_away, actual_home, actual_away, pts_exact=4, pts_diff=3, pts_tend=2):
    """
    Berechnet die Punkte nach Kicktipp-Regeln, nun mit flexiblen Punktewerten.
    """
    # 1. Exaktes Ergebnis
    if tip_home == actual_home and tip_away == actual_away:
        return pts_exact
        
    tip_diff = tip_home - tip_away
    actual_diff = actual_home - actual_away
    
    # Richtige Tordifferenz (Bei Unentschieden gibt es nur Tendenzpunkte, keine Differenzpunkte)
    if tip_diff == actual_diff:
        if tip_diff != 0:
            return pts_diff
        else:
            return pts_tend
        
    # Tendenz: Sieg Heimmannschaft
    if tip_home > tip_away and actual_home > actual_away:
        return pts_tend
        
    # Tendenz: Sieg Auswärtsmannschaft
    if tip_home < tip_away and actual_home < actual_away:
        return pts_tend
        
    return 0

def calculate_expected_value(tip_home, tip_away, normalized_probs, pts_exact=4, pts_diff=3, pts_tend=2):
    """
    Berechnet den Erwartungswert (EV) für einen bestimmten Tipp.
    Multipliziert die Wahrscheinlichkeit jedes möglichen Ergebnisses mit 
    den Punkten, die man für den Tipp bei diesem Ergebnis bekommen würde.
    """
    expected_value = 0.0
    
    for result_str, prob in normalized_probs.items():
        try:
            actual_home_str, actual_away_str = result_str.split(':')
            actual_home = int(actual_home_str.strip())
            actual_away = int(actual_away_str.strip())
            
            points = calculate_kicktipp_points(tip_home, tip_away, actual_home, actual_away, pts_exact, pts_diff, pts_tend)
            expected_value += points * prob
        except ValueError:
            # Ignoriere fehlerhafte Strings oder Sonderwetten ("Sonstige", etc.)
            continue
            
    return expected_value

def find_best_tips(normalized_probs, max_goals=6, pts_exact=4, pts_diff=3, pts_tend=2):
    """
    Spielt alle Tipps von 0:0 bis max_goals:max_goals durch und sortiert sie nach Erwartungswert.
    """
    results = []
    
    for tip_home in range(max_goals + 1):
        for tip_away in range(max_goals + 1):
            ev = calculate_expected_value(tip_home, tip_away, normalized_probs, pts_exact, pts_diff, pts_tend)
            results.append({
                "tip": f"{tip_home}:{tip_away}",
                "expected_value": ev
            })
            
    # Sortiere absteigend nach Erwartungswert
    results.sort(key=lambda x: x["expected_value"], reverse=True)
    return results

# Ein kleiner manueller Test, wenn das Skript direkt ausgeführt wird.
if __name__ == "__main__":
    # Fiktive Quoten für ein enges Spiel mit leichtem Heimvorteil
    dummy_odds = {
        "1:0": 7.5,
        "2:0": 10.0,
        "2:1": 9.0,
        "3:0": 20.0,
        "3:1": 18.0,
        "0:0": 9.5,
        "1:1": 6.5,
        "2:2": 15.0,
        "0:1": 9.0,
        "0:2": 15.0,
        "1:2": 11.0,
    }
    
    probs = normalize_odds(dummy_odds)
    print("Normalisierte Wahrscheinlichkeiten:")
    for res, p in probs.items():
        print(f"{res}: {p*100:.2f}%")
        
    print("\nBeste Tipps nach Erwartungswert:")
    best_tips = find_best_tips(probs, max_goals=4)
    for i, t in enumerate(best_tips[:10], 1):
        print(f"{i}. Tipp {t['tip']} -> Erwartungswert: {t['expected_value']:.3f} Punkte")
