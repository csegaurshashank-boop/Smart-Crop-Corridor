import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Leaf, LogOut, LayoutDashboard, Map, Bug, Users, Layers, Menu, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import LanguageSwitcher from './LanguageSwitcher'

export default function Sidebar({ role }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  const farmerLinks = [
    { to: '/dashboard', icon: <LayoutDashboard size={18} />, label: t('sidebar.dashboard') },
    { to: '/dashboard/crop-guidance', icon: <Map size={18} />, label: t('sidebar.cropGuidance') },
    { to: '/dashboard/pest-detection', icon: <Bug size={18} />, label: t('sidebar.pestDetection') },
  ]

  const managerLinks = [
    { to: '/manager-dashboard', icon: <LayoutDashboard size={18} />, label: t('sidebar.dashboard') },
    { to: '/manager-dashboard/fields', icon: <Layers size={18} />, label: t('sidebar.fields') },
    { to: '/manager-dashboard/farmers', icon: <Users size={18} />, label: t('sidebar.farmers') },
    { to: '/manager-dashboard/crop-guidance', icon: <Map size={18} />, label: t('sidebar.cropMonitoring') },
    { to: '/manager-dashboard/pest-detection', icon: <Bug size={18} />, label: t('sidebar.pestDetection') },
  ]

  const links = role === 'farmer' ? farmerLinks : managerLinks

  const sidebarContent = (
    <>
      <div className="p-6 border-b border-earth-800/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-crop-600 rounded-lg flex items-center justify-center">
            <Leaf size={16} className="text-white" />
          </div>
          <span className="font-display font-semibold text-earth-100">CropCorridor</span>
          {/* Close button — mobile only */}
          <button onClick={() => setOpen(false)} className="ml-auto lg:hidden p-1 text-earth-400 hover:text-earth-200">
            <X size={20} />
          </button>
        </div>
      </div>

      <div className="px-4 py-4 border-b border-earth-800/50">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 bg-earth-800 rounded-xl flex items-center justify-center">
            <span className="text-earth-300 font-body font-semibold text-sm">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </span>
          </div>
          <div>
            <div className="text-earth-200 text-sm font-body font-medium truncate max-w-[120px]">{user?.email || 'User'}</div>
            <div className={`text-xs font-body capitalize px-2 py-0.5 rounded-full inline-block mt-0.5 ${
              role === 'farmer' ? 'bg-crop-900/50 text-crop-400' : 'bg-soil-900/50 text-soil-400'
            }`}>{role}</div>
          </div>
        </div>
        {/* Language switcher inside sidebar */}
        <LanguageSwitcher className="w-full justify-center" />
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to}
            end={link.to.split('/').length <= 2}
            onClick={() => setOpen(false)}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            {link.icon}{link.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-earth-800/50">
        <button onClick={() => { logout(); navigate('/') }}
          className="nav-link w-full text-red-500/70 hover:text-red-400 hover:bg-red-900/20">
          <LogOut size={18} /> {t('sidebar.signOut')}
        </button>
      </div>
    </>
  )

  return (
    <>
      {/* Hamburger button — mobile only */}
      <button
        onClick={() => setOpen(true)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 bg-earth-900 border border-earth-700 rounded-xl text-earth-300 hover:text-earth-100 shadow-lg"
        aria-label="Open menu"
      >
        <Menu size={22} />
      </button>

      {/* Desktop sidebar — always visible on lg+ */}
      <aside className="hidden lg:flex w-60 min-h-screen bg-earth-950 border-r border-earth-800/50 flex-col fixed left-0 top-0 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile overlay sidebar */}
      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setOpen(false)} />
          {/* Drawer */}
          <aside className="fixed left-0 top-0 w-72 h-full bg-earth-950 border-r border-earth-800/50 flex flex-col z-50 lg:hidden animate-slide-in">
            {sidebarContent}
          </aside>
        </>
      )}
    </>
  )
}