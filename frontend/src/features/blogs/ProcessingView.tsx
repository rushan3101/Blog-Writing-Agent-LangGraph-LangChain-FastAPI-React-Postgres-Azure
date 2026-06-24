import type {StreamStep} from "../../types/blog";

interface Props {
  steps: StreamStep[];
}

export default function ProcessingView({
  steps,
}: Props) {

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-8">

      <h2 className="mb-8 text-2xl font-bold text-white">
        Creating Blog
      </h2>

      <div className="space-y-4">

        {steps.map((step) => (

          <div
            key={step.label}
            className="flex items-center gap-4"
          >

            {step.status ===
              "running" && (

              <div
                className="
                  h-4
                  w-4
                  animate-spin
                  rounded-full
                  border-2
                  border-blue-500
                  border-t-transparent
                "
              />

            )}

            {step.status ===
              "completed" && (

              <div
                className="
                  text-green-500
                "
              >
                ✓
              </div>

            )}

            <span
              className="
                text-gray-200
              "
            >
              {step.label}
            </span>

          </div>

        ))}

      </div>

    </div>
  );
}