import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio

# --- إعدادات البوت والآيديات ---
TOKEN = "MTU2MjI3NjcwNjYzMzY1NDQwMg.Ga_VJW.QDbWAlpA0G_pSkB2aSiYbMwfwd4EMyvZCBbRSc"
SETUP_CHANNEL_ID = 1526508851250200636
CATEGORY_ID = 1526508535771435008
SUPPORT_ROLE_ID = 1562405061068329061
RATING_CHANNEL_ID = 1562345502329274468

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- أزرار التقييم داخل التكت قبل الإغلاق ---
class RatingView(View):
    def __init__(self, ticket_author, closer):
        super().__init__(timeout=None)
        self.ticket_author = ticket_author
        self.closer = closer

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ticket_author and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا التقييم مخصص لصاحب التكت فقط!", ephemeral=True)
            return False
        return True

    async def process_rating(self, interaction: discord.Interaction, rating_str: str):
        rating_channel = interaction.guild.get_channel(RATING_CHANNEL_ID)
        if rating_channel:
            embed = discord.Embed(
                title="🌟 تقييم خدمة جديد | Cent Store",
                color=discord.Color.gold()
            )
            embed.add_field(name="👤 العضو", value=self.ticket_author.mention, inline=True)
            embed.add_field(name="🛠️ الإداري المسؤول", value=self.closer.mention, inline=True)
            embed.add_field(name="⭐ التقييم", value=rating_str, inline=False)
            embed.set_footer(text="Cent Store - شكراً لتعاملكم معنا ❤️")
            await rating_channel.send(embed=embed)

        await interaction.response.send_message("✅ تم تسجيل تقييمك بنجاح! سيتم إغلاق التكت خلال 3 ثوانٍ...")
        
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await asyncio.sleep(3)
        await interaction.channel.delete()

    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.red, custom_id="rate_1")
    async def star_1(self, interaction: discord.Interaction, button: Button):
        await self.process_rating(interaction, "⭐ (1/5)")

    @discord.ui.button(label="⭐⭐ 2", style=discord.ButtonStyle.blurple, custom_id="rate_2")
    async def star_2(self, interaction: discord.Interaction, button: Button):
        await self.process_rating(interaction, "⭐⭐ (2/5)")

    @discord.ui.button(label="⭐⭐⭐ 3", style=discord.ButtonStyle.blurple, custom_id="rate_3")
    async def star_3(self, interaction: discord.Interaction, button: Button):
        await self.process_rating(interaction, "⭐⭐⭐ (3/5)")

    @discord.ui.button(label="⭐⭐⭐⭐ 4", style=discord.ButtonStyle.green, custom_id="rate_4")
    async def star_4(self, interaction: discord.Interaction, button: Button):
        await self.process_rating(interaction, "⭐⭐⭐⭐ (4/5)")

    @discord.ui.button(label="⭐⭐⭐⭐⭐ 5", style=discord.ButtonStyle.green, custom_id="rate_5")
    async def star_5(self, interaction: discord.Interaction, button: Button):
        await self.process_rating(interaction, "⭐⭐⭐⭐⭐ (5/5)")

    @discord.ui.button(label="🔒 إغلاق بدون تقييم", style=discord.ButtonStyle.gray, custom_id="force_close", row=1)
    async def force_close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 جاري إغلاق التكت بدون تقييم...")
        await asyncio.sleep(2)
        await interaction.channel.delete()


# --- زر طلب الإغلاق من الإداري ---
class CloseTicketView(View):
    def __init__(self, ticket_author=None):
        super().__init__(timeout=None)
        self.ticket_author = ticket_author

    @discord.ui.button(label="🔒 إغلاق التكت", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        
        is_support = (support_role in interaction.user.roles) if support_role else False
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_support or is_admin):
            await interaction.response.send_message("❌ هذا الخيار مخصص لفريق الدعم والإدارة فقط!", ephemeral=True)
            return

        author = self.ticket_author
        if not author:
            for member in interaction.channel.members:
                if not member.bot and member != interaction.user:
                    author = member
                    break
            if not author:
                author = interaction.user

        embed = discord.Embed(
            title="📊 تقييم الخدمة | Cent Store",
            description=f"عزيزي {author.mention}، نرجو منك تقييم تجربة الخدمة معنا بالضغط على أحد الأزرار أدناه لتسهيل عملية إغلاق التكت.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Cent Store - رأيك يهمنا دائماً ✨")
        
        await interaction.response.send_message(
            content=f"{author.mention}",
            embed=embed,
            view=RatingView(ticket_author=author, closer=interaction.user)
        )


# --- نافذة الأسئلة المنبثقة عند فتح التكت ---
class TicketModal(Modal, title="📝 نموذج طلب الشراء - Cent Store"):
    order = TextInput(
        label="طلبك :",
        placeholder="اكتب المنتج أو الخدمة التي تريدها...",
        style=discord.TextStyle.short,
        required=True
    )
    quantity = TextInput(
        label="الكمية :",
        placeholder="مثال: 1, 5, 100...",
        style=discord.TextStyle.short,
        required=True
    )
    payment_method = TextInput(
        label="طريقة دفعك :",
        placeholder="مثال: مدى, سوا, STC Pay, الراجحي, بايبال...",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        support_role = guild.get_role(SUPPORT_ROLE_ID)

        if not category:
            await interaction.response.send_message("❌ خطأ: لم يتم العثور على الكاتيجوري المطلوب!", ephemeral=True)
            return

        # تحديد الصلاحيات
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # إنشاء القناة
        channel_name = f"ticket-{interaction.user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        # تجهيز الإنبد الفخم للتكت
        embed = discord.Embed(
            title="🎫 تكت طلب جديدة | Cent Store",
            description=f"مرحباً بك {interaction.user.mention} في **Cent Store**! ❤️\nتم إرسال تفاصيل طلبك بنجاح، وسيقوم فريق الدعم بالتواصل معك فوراً.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📦 الطلب", value=f"```{self.order.value}```", inline=False)
        embed.add_field(name="🔢 الكمية", value=f"```{self.quantity.value}```", inline=True)
        embed.add_field(name="💳 طريقة الدفع", value=f"```{self.payment_method.value}```", inline=True)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Cent Store Support System • يرجى الانتظار لحين رد الإدارة")

        # إرسال الرسالة والمنشن بروم التكت
        await ticket_channel.send(
            content=f"{interaction.user.mention} | {support_role.mention if support_role else ''}",
            embed=embed,
            view=CloseTicketView(ticket_author=interaction.user)
        )

        await interaction.response.send_message(f"✅ تم فتح التكت بنجاح: {ticket_channel.mention}", ephemeral=True)


# --- زر فتح التكت الرئيسي ---
class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 افتح تكت", style=discord.ButtonStyle.green, custom_id="open_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        # إظهار نافذة الأسئلة فوراً عند الضغط
        await interaction.response.send_modal(TicketModal())


# --- الأحداث والأوامر النصية ---
@bot.event
async def on_ready():
    bot.add_view(TicketSetupView())
    bot.add_view(CloseTicketView())
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Cent Store Bot is Online and Ready! 🚀")

# أمر إرسال البانل يدوياً (للتأكد والضمان)
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 Cent Store | مركز الدعم والخدمة",
        description=(
            "أهلاً بكم في متجر **Cent Store**! 🚀\n\n"
            "للبدء في عملية الشراء أو الاستفسار، يرجى الضغط على الزر أدناه ملء البيانات المطلوبة لفتح تكت تواصل مباشرة مع الإدارة."
        ),
        color=discord.Color.blue()
    )
    if bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    embed.set_footer(text="Cent Store • Best Quality & Fast Service")
    
    await ctx.channel.send(embed=embed, view=TicketSetupView())
    await ctx.message.delete()

# أمر لإضافة عضو للتكت
@bot.command()
@commands.has_permissions(manage_channels=True)
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
    await ctx.send(f"✅ تم إضافة {member.mention} إلى التكت.")

# أمر لإزالة عضو من التكت
@bot.command()
@commands.has_permissions(manage_channels=True)
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"🚫 تم إزالة {member.mention} من التكت.")

# تشغيل البوت
bot.run(TOKEN)
