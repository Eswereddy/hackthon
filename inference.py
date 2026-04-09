import sys
import traceback
from baseline_inference import main


if __name__ == "__main__":
    try:
        # Ensure stdout is flushed for structured output
        sys.stdout.flush()
        main()
        sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user", flush=True)
        sys.stdout.flush()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR in inference.py: {type(e).__name__}", flush=True)
        print(f"Details: {str(e)}", flush=True)
        print("\nFull traceback:", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)

