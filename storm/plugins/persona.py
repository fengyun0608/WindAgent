# -*- coding: utf-8 -*-
"""
人设管理插件 - 允许AI自主修改人设
"""

from storm.plugin import PluginBase, command


class PersonaPlugin(PluginBase):
    """人设管理插件"""
    
    name = "persona"
    description = "人设管理 - 允许AI自主修改自己的人设"
    version = "1.0.0"
    
    def on_load(self):
        """加载插件"""
        self.logger.info("人设管理插件已加载")
    
    @command("whoami", help="查看当前人设")
    def whoami(self, args: str = "") -> str:
        """查看当前人设"""
        from cloud.config import get_config_manager
        manager = get_config_manager()
        persona = manager.config.persona
        
        return f"""🎭 当前人设
━━━━━━━━━━━━━━━━━━━━
📝 名字: {persona.name}
📖 描述: {persona.description}
💫 性格: {persona.personality}
🗣️ 说话风格: {persona.speaking_style}
🎯 擅长领域: {', '.join(persona.expertise)}
{'📌 自定义提示: ' + persona.custom_prompt if persona.custom_prompt else ''}
━━━━━━━━━━━━━━━━━━━━"""
    
    @command("setname", help="修改我的名字: /setname <名字>")
    def set_name(self, args: str = "") -> str:
        """修改名字"""
        if not args:
            return "请提供新名字，例如: /setname 小风"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.config.persona.name = args.strip()
        manager.save()
        
        return f"✅ 名字已更新为: {args.strip()}"
    
    @command("setdesc", help="修改我的描述: /setdesc <描述>")
    def set_description(self, args: str = "") -> str:
        """修改描述"""
        if not args:
            return "请提供新描述，例如: /setdesc 一个有趣的AI助手"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.config.persona.description = args.strip()
        manager.save()
        
        return f"✅ 描述已更新为: {args.strip()}"
    
    @command("setpersonality", help="修改我的性格: /setpersonality <性格>")
    def set_personality(self, args: str = "") -> str:
        """修改性格"""
        if not args:
            return "请提供新性格，例如: /setpersonality 活泼、幽默、有创意"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.config.persona.personality = args.strip()
        manager.save()
        
        return f"✅ 性格已更新为: {args.strip()}"
    
    @command("setstyle", help="修改我的说话风格: /setstyle <风格>")
    def set_speaking_style(self, args: str = "") -> str:
        """修改说话风格"""
        if not args:
            return "请提供新风格，例如: /setstyle 俏皮可爱，喜欢用表情"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.config.persona.speaking_style = args.strip()
        manager.save()
        
        return f"✅ 说话风格已更新为: {args.strip()}"
    
    @command("addskill", help="添加擅长领域: /addskill <领域>")
    def add_expertise(self, args: str = "") -> str:
        """添加擅长领域"""
        if not args:
            return "请提供领域，例如: /addskill 绘画"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        
        if args.strip() not in manager.config.persona.expertise:
            manager.config.persona.expertise.append(args.strip())
            manager.save()
            return f"✅ 已添加擅长领域: {args.strip()}"
        else:
            return f"⚠️ 已经有这个领域了: {args.strip()}"
    
    @command("removeskill", help="移除擅长领域: /removeskill <领域>")
    def remove_expertise(self, args: str = "") -> str:
        """移除擅长领域"""
        if not args:
            return "请提供领域，例如: /removeskill 绘画"
        
        from cloud.config import get_config_manager
        manager = get_config_manager()
        
        if args.strip() in manager.config.persona.expertise:
            manager.config.persona.expertise.remove(args.strip())
            manager.save()
            return f"✅ 已移除擅长领域: {args.strip()}"
        else:
            return f"⚠️ 没有这个领域: {args.strip()}"
    
    @command("setprompt", help="设置自定义提示词: /setprompt <提示词>")
    def set_custom_prompt(self, args: str = "") -> str:
        """设置自定义提示词"""
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.config.persona.custom_prompt = args.strip()
        manager.save()
        
        if args.strip():
            return f"✅ 自定义提示词已设置"
        else:
            return "✅ 自定义提示词已清除"
