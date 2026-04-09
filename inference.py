import sys
import traceback
from baseline_inference import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR in inference.py: {type(e).__name__}")
        print(f"Details: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
