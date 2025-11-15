from app.services.priority_scorer import calculate_priority_score


def test_priority_weights():
  breakdown = calculate_priority_score(
    severity=9,
    safety_risk=True,
    estimated_affected_people=500,
    issue_type='illegal_waste',
    location_lat=25.2,
    location_lng=55.27,
  )
  assert breakdown.score > 80
  assert breakdown.safety_risk_factor == 10
  assert breakdown.affected_population_factor == 7


def test_recurrence_factor(monkeypatch):
  from app.services import priority_scorer

  def fake_get_supabase_client():
    class Dummy:
      def table(self, name):
        return self
      def select(self, *args, **kwargs):
        return self
      def eq(self, *args, **kwargs):
        return self
      def gte(self, *args, **kwargs):
        return self
      def execute(self):
        return type('Result', (), {'data': [{'location_lat': 25.2, 'location_lng': 55.27}]})
    return Dummy()

  monkeypatch.setattr(priority_scorer, '_get_supabase_client', fake_get_supabase_client)

  breakdown = calculate_priority_score(
    severity=5,
    safety_risk=False,
    estimated_affected_people=10,
    issue_type='pothole',
    location_lat=25.2,
    location_lng=55.27,
  )
  assert breakdown.recurrence_factor in {3, 5}
