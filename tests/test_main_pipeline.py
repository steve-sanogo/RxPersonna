from main import run_pipeline

def test_run_pipeline_executes():

    df = run_pipeline()

    assert df is not None
    assert len(df) > 0
    assert "graphml" in df.columns