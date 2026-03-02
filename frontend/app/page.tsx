"use client";

import { useState } from "react";

interface OptimizedOption {
  optimized_items: string[];
  total_price: number;
  deals_used: string[];
}

interface OptimizeResponse {
  options: OptimizedOption[];
}

export default function Home() {
  const [restaurantId, setRestaurantId] = useState("mcdonalds");
  const [ingredientRequirements, setIngredientRequirements] = useState("");
  const [itemRequirements, setItemRequirements] = useState("");
  const [rewardsPoints, setRewardsPoints] = useState("0");
  const [results, setResults] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/optimize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          restaurant_id: restaurantId,
          ingredient_requirements: ingredientRequirements
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s),
          item_requirements: itemRequirements
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s),
          rewards_points: parseInt(rewardsPoints) || 0,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: OptimizeResponse = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to optimize order");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Fast Food Value Optimizer
        </h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="restaurant"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Restaurant
              </label>
              <select
                id="restaurant"
                value={restaurantId}
                onChange={(e) => setRestaurantId(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 text-base bg-white"
              >
                <option value="mcdonalds">McDonald's</option>
                <option value="tacobell">Taco Bell</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="items"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Item Requirements (comma-separated)
              </label>
              <input
                id="items"
                type="text"
                value={itemRequirements}
                onChange={(e) => setItemRequirements(e.target.value)}
                placeholder="e.g., big_mac, medium_fries"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 text-base bg-white placeholder:text-gray-400"
              />
              <p className="mt-1 text-sm text-gray-500">
                Enter specific items you want (use item slugs)
              </p>
            </div>

            <div>
              <label
                htmlFor="ingredients"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Ingredient Requirements (comma-separated)
              </label>
              <input
                id="ingredients"
                type="text"
                value={ingredientRequirements}
                onChange={(e) => setIngredientRequirements(e.target.value)}
                placeholder="e.g., chicken, lettuce, cheese"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 text-base bg-white placeholder:text-gray-400"
              />
              <p className="mt-1 text-sm text-gray-500">
                Enter ingredients you want in your order
              </p>
            </div>

            <div>
              <label
                htmlFor="points"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Rewards Points
              </label>
              <input
                id="points"
                type="number"
                value={rewardsPoints}
                onChange={(e) => setRewardsPoints(e.target.value)}
                min="0"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 text-base bg-white"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Optimizing..." : "Find Best Deals"}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        {results && results.options && results.options.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Optimized Options
            </h2>
            {results.options.map((option, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-gray-900">
                    Option {index + 1}
                  </h3>
                  <span className="text-2xl font-bold text-green-600">
                    ${option.total_price.toFixed(2)}
                  </span>
                </div>

                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Items:
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {option.optimized_items.map((item, itemIndex) => (
                      <li key={itemIndex} className="text-gray-600">
                        {item.replace(/_/g, " ")}
                      </li>
                    ))}
                  </ul>
                </div>

                {option.deals_used.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Deals Applied:
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {option.deals_used.map((deal, dealIndex) => (
                        <span
                          key={dealIndex}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          {deal.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}