import * as tf from '@tensorflow/tfjs';

interface ComplexityResult {
  complexity: 'TRIVIAL' | 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'EXPERT';
  confidence: number;
  estimatedTokens: number;
  suggestedModel: string;
}

class ComplexityEstimator {
  private model: tf.LayersModel | null = null;
  private isLoading = false;
  private loadPromise: Promise<void> | null = null;

  async ensureModelLoaded(): Promise<void> {
    if (this.model) return;

    if (this.loadPromise) {
      return this.loadPromise;
    }

    this.isLoading = true;
    this.loadPromise = (async () => {
      try {
        console.log('Loading complexity estimation model...');
        this.model = await tf.loadLayersModel('/models/complexity-estimator/model.json');
        console.log('Complexity estimator model loaded successfully');
      } catch (error) {
        console.error('Failed to load complexity model:', error);
        this.model = null;
      } finally {
        this.isLoading = false;
      }
    })();

    return this.loadPromise;
  }

  private preprocessText(text: string): tf.Tensor {
    const words = text
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .split(/\s+/)
      .filter((w) => w.length > 0)
      .slice(0, 128);

    const vector = new Array(128).fill(0);
    words.forEach((word, idx) => {
      const hash = word.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      vector[idx] = (hash % 1000) / 1000;
    });

    return tf.tensor2d([vector], [1, 128]);
  }

  async estimate(query: string): Promise<ComplexityResult> {
    await this.ensureModelLoaded();

    if (!this.model) {
      return this.ruleBasedEstimation(query);
    }

    try {
      const inputTensor = this.preprocessText(query);
      const prediction = this.model.predict(inputTensor) as tf.Tensor;
      const probabilities = await prediction.data();

      inputTensor.dispose();
      prediction.dispose();

      const maxIdx = probabilities.indexOf(Math.max(...Array.from(probabilities)));
      const complexityLevels: Array<
        'TRIVIAL' | 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'EXPERT'
      > = ['TRIVIAL', 'SIMPLE', 'MODERATE', 'COMPLEX', 'EXPERT'];

      const complexity = complexityLevels[maxIdx];
      const confidence = probabilities[maxIdx];
      const estimatedTokens = Math.ceil(query.split(/\s+/).length * 1.3);

      const modelMap: Record<string, string> = {
        TRIVIAL: 'NANO_1B',
        SIMPLE: 'SMALL_3B',
        MODERATE: 'MEDIUM_7B',
        COMPLEX: 'LARGE_13B',
        EXPERT: 'XL_34B',
      };

      return {
        complexity,
        confidence,
        estimatedTokens,
        suggestedModel: modelMap[complexity],
      };
    } catch (error) {
      console.error('ML estimation failed, using fallback:', error);
      return this.ruleBasedEstimation(query);
    }
  }

  private ruleBasedEstimation(query: string): ComplexityResult {
    const wordCount = query.split(/\s+/).length;
    const hasComplexPatterns = /analyze|compare|evaluate|design|implement|optimize/i.test(query);
    const hasExpertPatterns = /prove|derive|develop.*novel|create.*revolutionary/i.test(query);
    const hasCodePatterns = /code|function|algorithm|api|debug/i.test(query);

    let complexity: ComplexityResult['complexity'] = 'MODERATE';
    let confidence = 0.6;

    if (hasExpertPatterns) {
      complexity = 'EXPERT';
      confidence = 0.75;
    } else if (hasComplexPatterns || hasCodePatterns) {
      complexity = 'COMPLEX';
      confidence = 0.7;
    } else if (wordCount < 10) {
      complexity = 'SIMPLE';
      confidence = 0.65;
    } else if (wordCount < 5) {
      complexity = 'TRIVIAL';
      confidence = 0.7;
    }

    return {
      complexity,
      confidence,
      estimatedTokens: Math.ceil(wordCount * 1.3),
      suggestedModel: {
        TRIVIAL: 'NANO_1B',
        SIMPLE: 'SMALL_3B',
        MODERATE: 'MEDIUM_7B',
        COMPLEX: 'LARGE_13B',
        EXPERT: 'XL_34B',
      }[complexity] as string,
    };
  }

  dispose() {
    if (this.model) {
      this.model.dispose();
      this.model = null;
    }
  }
}

export const complexityEstimator = new ComplexityEstimator();
