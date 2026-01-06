# feat: 添加用户手动触发新手引导功能

## 概述

为 OpportunityRadar 添加用户界面入口，允许用户主动触发/重新播放新手引导教程。

## 背景

当前实现：
- 新手引导仅在首次访问时自动触发
- 完成后存储到 localStorage，不再显示
- 用户无法主动重新查看引导

用户需求：
- 新用户可能跳过引导后想重新查看
- 老用户可能需要重新了解某些功能
- 提高产品的可发现性和易用性

## 研究发现

### 现有实现分析

| 文件 | 功能 |
|------|------|
| `frontend/stores/tour-store.ts` | Zustand store，管理引导状态 |
| `frontend/components/tours/dashboard-tour.tsx` | Dashboard 引导组件 |
| `frontend/app/(dashboard)/settings/page.tsx` | 设置页面（已有引导管理区域） |

### 关键发现

**已实现的功能：**
- ✅ `useTourStore.resetTours()` - 重置所有引导
- ✅ `useTourStore.markTourComplete(tourId)` - 标记完成
- ✅ `useTourStore.isTourComplete(tourId)` - 检查状态
- ✅ 设置页面有 "Guided Tours" 区域

**缺失的功能：**
- ❌ Dashboard 页面无触发入口
- ❌ 全局导航无帮助按钮
- ❌ 移动端无引导入口

### Driver.js API

```typescript
// 手动触发引导
const driverObj = driver({ steps: [...] });
driverObj.drive();      // 开始引导
driverObj.destroy();    // 销毁引导
driverObj.moveNext();   // 下一步
driverObj.moveTo(n);    // 跳转到第n步
```

## 实施方案

### 方案选择

| 方案 | 位置 | 优点 | 缺点 | 优先级 |
|------|------|------|------|--------|
| A | Dashboard 标题栏帮助图标 | 上下文相关、易发现 | 仅 Dashboard 可见 | **推荐** |
| B | 全局导航帮助菜单 | 全局可用 | 需要多处修改 | 次选 |
| C | 悬浮帮助按钮 | 始终可见 | 占用空间、可能干扰 | 可选 |
| D | 设置页面（已有） | 符合预期 | 发现性差 | 已实现 |

### 推荐实施：方案 A + 增强设置页面

## 详细设计

### 1. Dashboard 帮助按钮

**位置**: Dashboard 页面标题右侧

**UI 设计**:
```
┌─────────────────────────────────────────┐
│  Dashboard                    [?] [⚙️]  │
│  ─────────────────────────────────────  │
```

**文件修改**: `frontend/app/(dashboard)/dashboard/page.tsx`

```tsx
import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTourStore } from "@/stores/tour-store";

function DashboardHeader() {
  const { hasCompletedDashboardTour } = useTourStore();

  const handleRestartTour = () => {
    useTourStore.setState({ hasCompletedDashboardTour: false });
    // 刷新页面触发引导
    window.location.reload();
  };

  return (
    <div className="flex items-center justify-between mb-6">
      <h1 data-tour="welcome" className="text-2xl font-bold">
        Dashboard
      </h1>
      <Button
        variant="ghost"
        size="icon"
        onClick={handleRestartTour}
        title="Replay tutorial"
        aria-label="Replay dashboard tutorial"
      >
        <HelpCircle className="h-5 w-5" />
      </Button>
    </div>
  );
}
```

### 2. 优化引导组件（无需刷新）

**文件修改**: `frontend/components/tours/dashboard-tour.tsx`

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { driver, type Driver } from "driver.js";
import { useTourStore } from "@/stores/tour-store";

// 导出启动函数供外部调用
export function useDashboardTour() {
  const { hasCompletedDashboardTour, markTourComplete } = useTourStore();
  const [driverInstance, setDriverInstance] = useState<Driver | null>(null);

  const startTour = useCallback(() => {
    const driverObj = driver({
      showProgress: true,
      allowClose: true,
      doneBtnText: "Got it!",
      nextBtnText: "Next",
      prevBtnText: "Back",
      steps: [
        // ... 现有步骤
      ],
      onDestroyed: () => {
        markTourComplete("dashboard");
      },
    });

    setDriverInstance(driverObj);
    driverObj.drive();
  }, [markTourComplete]);

  return { startTour, hasCompletedDashboardTour };
}

export function DashboardTour() {
  const { hasCompletedDashboardTour, markTourComplete } = useTourStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || hasCompletedDashboardTour) return;

    const timer = setTimeout(() => {
      const driverObj = driver({
        // ... 现有配置
      });
      driverObj.drive();
    }, 800);

    return () => clearTimeout(timer);
  }, [mounted, hasCompletedDashboardTour, markTourComplete]);

  return null;
}
```

### 3. 创建可复用的帮助按钮组件

**新建文件**: `frontend/components/ui/help-button.tsx`

```tsx
"use client";

import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface HelpButtonProps {
  onTrigger: () => void;
  label?: string;
  tooltipText?: string;
}

export function HelpButton({
  onTrigger,
  label,
  tooltipText = "Show tutorial",
}: HelpButtonProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={onTrigger}
            aria-label={label || tooltipText}
          >
            <HelpCircle className="h-5 w-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
```

### 4. 增强设置页面

**文件修改**: `frontend/app/(dashboard)/settings/page.tsx`

在 Guided Tours 区域添加更明显的入口：

```tsx
<Card className="p-6">
  <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
    <Sparkles className="h-5 w-5" />
    Guided Tours
  </h2>
  <p className="text-muted-foreground mb-4">
    Replay tutorials to learn about features
  </p>

  <div className="space-y-3">
    {/* Dashboard Tour */}
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-3">
        <LayoutDashboard className="h-5 w-5 text-muted-foreground" />
        <div>
          <p className="font-medium">Dashboard Tour</p>
          <p className="text-sm text-muted-foreground">
            Learn about the main dashboard
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {hasCompletedDashboardTour && (
          <span className="text-green-500 text-sm">✓ Completed</span>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleRestartTour("dashboard", "/dashboard")}
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Replay
        </Button>
      </div>
    </div>

    {/* 其他引导... */}
  </div>

  {/* 重置所有 */}
  <div className="mt-4 pt-4 border-t">
    <Button variant="ghost" size="sm" onClick={resetTours}>
      Reset all tours
    </Button>
  </div>
</Card>
```

## 验收标准

- [ ] Dashboard 页面右上角显示帮助图标 (?)
- [ ] 点击帮助图标可重新播放引导
- [ ] 引导不需要刷新页面即可启动
- [ ] 设置页面可查看和管理所有引导
- [ ] 移动端帮助图标可正常点击（≥44px）
- [ ] 按钮有 aria-label 和 tooltip
- [ ] 所有测试通过

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/components/ui/help-button.tsx` | 新建 | 可复用帮助按钮组件 |
| `frontend/components/tours/dashboard-tour.tsx` | 修改 | 导出 `useDashboardTour` hook |
| `frontend/app/(dashboard)/dashboard/page.tsx` | 修改 | 添加帮助按钮 |
| `frontend/app/(dashboard)/settings/page.tsx` | 修改 | 增强引导管理区域 |

## 时间估算

- 帮助按钮组件: ~30 分钟
- Dashboard 集成: ~20 分钟
- 设置页面增强: ~20 分钟
- 测试和调试: ~20 分钟

**总计: ~1.5 小时**

## 参考资料

- [Driver.js 官方文档](https://driverjs.com/)
- [WCAG 2.1 可访问性指南](https://www.w3.org/WAI/WCAG21/quickref/)
- 项目现有实现: `frontend/stores/tour-store.ts`
