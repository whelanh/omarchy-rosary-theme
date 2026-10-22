-- Rosary: antique gold to ultramarine on the focused window.
local active_border_color = { colors = { "rgba(d9b45bee)", "rgba(6f8fc9ee)" }, angle = 45 }
local inactive_border_color = "rgba(2a3048aa)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },
  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },
})
