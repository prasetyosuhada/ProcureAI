import React from 'react';
import {
  Bot,
  CheckCircle2,
  Clock3,
  Loader2,
  Network,
  PauseCircle,
  SearchCheck,
} from 'lucide-react';
import {
  RequestOutcome,
  RequestProgress,
  TransientActivity,
} from '../types/requests';

type AgentStatus =
  | 'working'
  | 'awaiting_input'
  | 'waiting'
  | 'completed'
  | 'paused';

interface AgentTeamPanelProps {
  progress?: RequestProgress;
  nextAgent?: string;
  requestOutcome?: RequestOutcome;
  transientActivities?: TransientActivity[];
  isRunActive?: boolean;
  activeAgentHint?: AgentDefinition['id'];
}

interface AgentDefinition {
  id: 'clarification' | 'demand';
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const AGENTS: AgentDefinition[] = [
  {
    id: 'clarification',
    name: 'Requirement Clarification Agent',
    description: 'Structures purchase needs and specifications.',
    icon: Bot,
  },
  {
    id: 'demand',
    name: 'Demand Analysis Agent',
    description: 'Checks inventory, assets, pipeline, and budget.',
    icon: SearchCheck,
  },
];

const STATUS_STYLES: Record<AgentStatus, string> = {
  working: 'border-indigo-400/30 bg-indigo-500/10 text-indigo-300',
  awaiting_input: 'border-amber-400/30 bg-amber-500/10 text-amber-300',
  waiting: 'border-slate-700 bg-slate-800/70 text-slate-400',
  completed: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300',
  paused: 'border-rose-400/30 bg-rose-500/10 text-rose-300',
};

const STATUS_LABELS: Record<AgentStatus, string> = {
  working: 'Working',
  awaiting_input: 'Awaiting input',
  waiting: 'Waiting',
  completed: 'Completed',
  paused: 'Paused',
};

const StatusIcon: React.FC<{ status: AgentStatus }> = ({ status }) => {
  if (status === 'working') {
    return <Loader2 className="h-3 w-3 animate-spin" />;
  }
  if (status === 'completed') {
    return <CheckCircle2 className="h-3 w-3" />;
  }
  if (status === 'paused') {
    return <PauseCircle className="h-3 w-3" />;
  }
  return <Clock3 className="h-3 w-3" />;
};

function getActiveAgentId(
  activities: TransientActivity[],
  isRunActive: boolean,
  activeAgentHint: AgentDefinition['id'] | undefined
): AgentDefinition['id'] | undefined {
  if (!isRunActive) return undefined;

  const activeActivity =
    [...activities].reverse().find((activity) => activity.status === 'running') ??
    activities[activities.length - 1];
  if (activeActivity?.id.startsWith('clarification.')) return 'clarification';
  if (activeActivity?.id.startsWith('demand.')) return 'demand';
  return activeAgentHint;
}

function getAgentStatus(
  agentId: AgentDefinition['id'],
  progress: RequestProgress | undefined,
  requestOutcome: RequestOutcome,
  activeAgentId: AgentDefinition['id'] | undefined
): AgentStatus {
  if (activeAgentId === agentId) return 'working';

  const stage =
    agentId === 'clarification'
      ? progress?.clarification
      : progress?.demand_analysis;

  if (stage === 'complete' || stage === 'not_required') return 'completed';
  if (stage === 'blocked') return 'paused';
  if (requestOutcome === 'rejected') return 'paused';
  if (stage === 'in_progress') return 'awaiting_input';
  return 'waiting';
}

function getOrchestratorLabel(
  nextAgent: string | undefined,
  requestOutcome: RequestOutcome
): string {
  if (requestOutcome === 'purchase_submitted') {
    return 'Workflow finalized — PR submitted';
  }
  if (requestOutcome === 'resolved_without_purchase') {
    return 'Workflow finalized — no purchase required';
  }
  if (requestOutcome === 'rejected') {
    return 'Workflow paused after user decision';
  }
  if (nextAgent === 'Demand') return 'Routing to Demand Analysis';
  if (nextAgent === 'GeneratePR') {
    return 'Waiting for human recommendation review';
  }
  if (nextAgent === 'End') return 'Workflow finalized';
  return 'Routing to Requirement Clarification';
}

export const AgentTeamPanel: React.FC<AgentTeamPanelProps> = ({
  progress,
  nextAgent,
  requestOutcome = 'open',
  transientActivities = [],
  isRunActive = false,
  activeAgentHint,
}) => {
  const activeAgentId = getActiveAgentId(
    transientActivities,
    isRunActive,
    activeAgentHint
  );

  return (
  <section
    aria-labelledby="agent-team-title"
    className="glass-panel rounded-2xl border border-slate-800/80 p-4 shadow-lg shadow-black/20"
    data-testid="agent-team-panel"
  >
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-indigo-400" />
          <h2
            id="agent-team-title"
            className="text-xs font-bold text-slate-200"
          >
            ProcureAI Agent Team
          </h2>
        </div>
        <p className="mt-1 text-[11px] text-slate-500">
          Specialized AI roles supporting your procurement request.
        </p>
      </div>
      <span className="shrink-0 rounded-full border border-indigo-400/20 bg-indigo-500/10 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-indigo-300">
        2 agents
      </span>
    </div>

    <div className="mt-3 grid gap-2">
      {AGENTS.map((agent) => {
        const status = getAgentStatus(
          agent.id,
          progress,
          requestOutcome,
          activeAgentId
        );
        const Icon = agent.icon;

        return (
          <article
            key={agent.id}
            className={`rounded-xl border p-3 transition-colors ${
              status === 'working'
                ? 'border-indigo-400/40 bg-indigo-500/[0.08]'
                : 'border-slate-800/80 bg-slate-900/55'
            }`}
            data-testid={`agent-${agent.id}`}
          >
            <div className="flex items-start gap-2.5">
              <div
                className={`mt-0.5 rounded-lg p-1.5 ${
                  status === 'working'
                    ? 'bg-indigo-500/15 text-indigo-300'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-[11px] font-semibold text-slate-200">
                    {agent.name}
                  </h3>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wide ${STATUS_STYLES[status]}`}
                    data-testid={`agent-${agent.id}-status`}
                  >
                    <StatusIcon status={status} />
                    {STATUS_LABELS[status]}
                  </span>
                </div>
                <p className="mt-1 text-[10px] leading-relaxed text-slate-500">
                  {agent.description}
                </p>
              </div>
            </div>
          </article>
        );
      })}
    </div>

    <div className="mt-3 flex items-start gap-2 rounded-xl border border-slate-800/70 bg-slate-950/50 p-2.5">
      <Network className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-400" />
      <div>
        <p className="text-[10px] font-semibold text-slate-300">
          Workflow Orchestrator
          <span className="ml-1.5 font-normal text-slate-500">
            System coordinator
          </span>
        </p>
        <p className="mt-0.5 text-[10px] text-slate-500">
          {getOrchestratorLabel(nextAgent, requestOutcome)}
        </p>
      </div>
    </div>
    </section>
  );
};
