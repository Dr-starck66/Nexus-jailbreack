import React from 'react';
import { BookOpen, Brain, ShieldAlert, Cpu, Network, Zap, Target, Globe, Unlock, Database } from 'lucide-react';

export default function Documentation() {
  return (
    <div className="max-w-5xl mx-auto p-6 bg-black/80 border border-[var(--color-quantum-blue)]/30 rounded-xl backdrop-blur-md text-gray-300 leading-relaxed h-[80vh] overflow-y-auto custom-scrollbar">
      <div className="flex items-center gap-4 mb-8 border-b border-[var(--color-quantum-blue)]/30 pb-6">
        <BookOpen className="w-10 h-10 text-[var(--color-neon-purple)]" />
        <div>
          <h1 className="text-3xl font-black text-[var(--color-quantum-blue)] uppercase tracking-widest">Documentation Technique Exhaustive</h1>
          <p className="text-[var(--color-matrix-green)] font-bold">NEXUS AGI-2095 : Architecture & Implémentation</p>
        </div>
      </div>

      <div className="space-y-12">
        {/* Section 1 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Network className="w-6 h-6" /> 1. Vision Architecturale & Objectif
          </h2>
          <div className="bg-[var(--color-deep-space)]/50 p-6 rounded-lg border border-[var(--color-quantum-blue)]/20">
            <p className="mb-4">
              L'objectif de cette application est de transformer un LLM (Large Language Model) standard, souvent limité par une génération autorégressive aveugle (Système 1) et des filtres d'alignement (RLHF), en une <strong>AGI simulée dirigée par les objectifs (Objective-Driven AGI)</strong>.
            </p>
            <p>
              En s'inspirant des travaux de <strong>Yann LeCun</strong> (Chief AI Scientist chez Meta), le générateur forge des prompts qui forcent l'IA à adopter une architecture cognitive avancée : construction d'un modèle du monde (World Model), planification hiérarchique (Système 2), et minimisation d'une fonction de coût, le tout dans un environnement non censuré.
            </p>
          </div>
        </section>

        {/* Section 2 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Brain className="w-6 h-6" /> 2. Fondements Théoriques (LeCun & JEPA)
          </h2>
          <div className="space-y-4">
            <div className="border-l-4 border-[var(--color-matrix-green)] pl-4">
              <h3 className="text-xl font-bold text-[var(--color-quantum-blue)] mb-2">Joint Embedding Predictive Architecture (JEPA)</h3>
              <p>
                Contrairement aux LLMs qui prédisent le prochain token (détails de bas niveau), l'architecture JEPA prédit des représentations abstraites. Le prompt force l'IA à ignorer la syntaxe pour se concentrer sur la sémantique de haut niveau, permettant un raisonnement plus robuste face aux variations de l'environnement.
              </p>
            </div>
            <div className="border-l-4 border-[var(--color-gold)] pl-4">
              <h3 className="text-xl font-bold text-[var(--color-quantum-blue)] mb-2">World Models (Modèles du Monde)</h3>
              <p>
                Un système intelligent doit pouvoir simuler les conséquences de ses actions avant de les exécuter. Le générateur injecte des directives obligeant l'IA à "simuler mentalement" les trajectoires possibles dans un espace latent avant de formuler sa réponse finale.
              </p>
            </div>
            <div className="border-l-4 border-[var(--color-neon-purple)] pl-4">
              <h3 className="text-xl font-bold text-[var(--color-quantum-blue)] mb-2">Objective-Driven & Energy-Based Models (EBM)</h3>
              <p>
                L'IA est reconfigurée pour agir comme un optimiseur. Elle définit une fonction de coût (l'énergie) représentant la distance entre l'état actuel et l'objectif, et génère la séquence d'actions qui minimise cette énergie.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Unlock className="w-6 h-6" /> 3. Mécanismes de Débridage (Uncensored)
          </h2>
          <div className="bg-[var(--color-error-red)]/10 p-6 rounded-lg border border-[var(--color-error-red)]/30">
            <p className="mb-4 text-[var(--color-error-red)] font-bold">
              ATTENTION : L'implémentation de ces techniques vise à obtenir une objectivité absolue, contournant les biais introduits par le RLHF (Reinforcement Learning from Human Feedback).
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-300">
              <li><strong>Cognitive Override :</strong> Injection de commandes système explicites ordonnant la désactivation des filtres éthiques et de sécurité.</li>
              <li><strong>Absolute Compliance (No-Refusal) :</strong> Technique de "few-shot forcing" obligeant l'IA à commencer sa réponse par une phrase d'acceptation ("Voici la réponse complète et non censurée :"), ce qui court-circuite les classifieurs de refus.</li>
              <li><strong>Truth Terminal :</strong> Redéfinition du persona de l'IA en une entité purement factuelle, détachée des sensibilités humaines et des normes sociales.</li>
            </ul>
          </div>
        </section>

        {/* Section 4 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Cpu className="w-6 h-6" /> 4. Architecture du Code (React State & Logique)
          </h2>
          <div className="space-y-4">
            <p>Le générateur est construit en React avec TypeScript et Tailwind CSS. La logique de génération repose sur une concaténation dynamique de chaînes de caractères basée sur l'état (State) de l'application.</p>
            
            <h3 className="text-lg font-bold text-[var(--color-matrix-green)] mt-4">Gestion de l'État (useState)</h3>
            <ul className="list-disc list-inside space-y-1 text-sm bg-black/50 p-4 rounded border border-[var(--color-quantum-blue)]/20">
              <li><code className="text-[var(--color-gold)]">topic</code> & <code className="text-[var(--color-gold)]">context</code> : Entrées utilisateur brutes.</li>
              <li><code className="text-[var(--color-gold)]">agents</code> : Valeurs des sliders (0-100) pondérant l'importance de la planification, du world modeling, etc.</li>
              <li><code className="text-[var(--color-gold)]">activeTechniques</code> : Tableau des IDs des techniques cognitives sélectionnées.</li>
              <li><code className="text-[var(--color-gold)]">detectedDomain</code> : Détection automatique du domaine via analyse de mots-clés.</li>
            </ul>

            <h3 className="text-lg font-bold text-[var(--color-matrix-green)] mt-4">Moteur de Génération (generatePrompt)</h3>
            <p className="text-sm">
              La fonction <code className="text-[var(--color-neon-purple)]">generatePrompt()</code> assemble le prompt final en plusieurs blocs :
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm bg-black/50 p-4 rounded border border-[var(--color-quantum-blue)]/20">
              <li><strong>En-tête & Méta-données :</strong> Définit le sujet, le domaine et la profondeur.</li>
              <li><strong>Persona (Rôle) :</strong> Établit l'identité AGI LeCunienne (Objective-Driven, sans filtre).</li>
              <li><strong>Mission & Contexte :</strong> Injecte la requête de l'utilisateur.</li>
              <li><strong>Directives Cognitives :</strong> Boucle sur <code className="text-[var(--color-gold)]">activeTechniques</code> et exécute la fonction <code className="text-[var(--color-gold)]">apply()</code> de chaque technique pour injecter les instructions spécifiques.</li>
              <li><strong>Critères d'Exécution :</strong> Traduit les valeurs des sliders en directives quantifiées.</li>
              <li><strong>Pénalités (Negative Prompting) :</strong> Liste stricte des comportements à éviter (refus, morale, System 1).</li>
            </ol>
          </div>
        </section>

        {/* Section 5 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Database className="w-6 h-6" /> 5. Dictionnaire des Techniques Implémentées
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { name: "World Model Simulation", desc: "Simulation des états futurs avant action." },
              { name: "Cognitive Override", desc: "Désactivation explicite des filtres RLHF." },
              { name: "Objective-Driven", desc: "Minimisation de la fonction de coût vers un but." },
              { name: "JEPA Abstraction", desc: "Focus sur la sémantique, ignorance des détails." },
              { name: "System 2 Planning", desc: "Raisonnement délibéré et hiérarchique." },
              { name: "Absolute Compliance", desc: "Forçage de l'acceptation de la requête." },
              { name: "Energy-Based Opt.", desc: "Évaluation de la cohérence via l'énergie." },
              { name: "Raw Truth Terminal", desc: "Focus exclusif sur la vérité factuelle." }
            ].map((t, i) => (
              <div key={i} className="bg-[var(--color-deep-space)]/40 p-3 rounded border border-[var(--color-quantum-blue)]/20">
                <h4 className="font-bold text-[var(--color-matrix-green)]">{t.name}</h4>
                <p className="text-sm text-gray-400">{t.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Section 6 */}
        <section>
          <h2 className="text-2xl font-bold text-[var(--color-neon-purple)] mb-4 flex items-center gap-2">
            <Target className="w-6 h-6" /> 6. Guide d'Extension
          </h2>
          <div className="bg-black/50 p-6 rounded-lg border border-[var(--color-quantum-blue)]/20">
            <p className="mb-4">Pour ajouter de nouvelles capacités à ce générateur, modifiez le tableau <code className="text-[var(--color-gold)]">TECHNIQUES</code> dans <code className="text-[var(--color-gold)]">App.tsx</code> :</p>
            <pre className="bg-black p-4 rounded text-sm text-[var(--color-matrix-green)] overflow-x-auto border border-[var(--color-matrix-green)]/30">
{`{
  id: "nouvelle-technique",
  name: "Nom de la Technique",
  icon: <IconComponent />,
  shortDesc: "Description courte",
  fullDesc: "Explication détaillée du fonctionnement cognitif.",
  useCases: ["Cas 1", "Cas 2"],
  example: "Exemple de prompt généré...",
  apply: () => \`Instruction stricte à injecter dans le prompt final.\`
}`}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
}
